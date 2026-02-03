import inspect
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from types import CoroutineType
from typing import TYPE_CHECKING, NamedTuple

from robyn.authentication import AuthenticationHandler, AuthenticationNotConfiguredError
from robyn.dependency_injection import DependencyMap
from robyn.jsonify import jsonify
from robyn.openapi import OpenAPI
from robyn.responses import FileResponse, StreamingResponse
from robyn.robyn import FunctionInfo, Headers, HttpMethod, Identity, MiddlewareType, QueryParams, Request, Response, Url
from robyn.types import Body, Files, FormData, IPAddress, Method, PathParams
from robyn.ws import WebSocket

from . import status_codes

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from robyn import SubRouter


def lower_http_method(method: HttpMethod):
    return (str(method))[11:].lower()


class Route(NamedTuple):
    route_type: HttpMethod
    route: str
    function: FunctionInfo
    is_const: bool
    auth_required: bool
    openapi_name: str
    openapi_tags: list[str]


class RouteMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    route: str
    function: FunctionInfo
    route_type: HttpMethod


class GlobalMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    function: FunctionInfo


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args) -> Callable | CoroutineType | WebSocket: ...


class Router(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes: list[Route] = []

    def _format_tuple_response(self, res: tuple) -> Response:
        if len(res) != 3:
            raise ValueError("Tuple should have 3 elements")

        description, headers, status_code = res
        formatted = self._format_response(description)
        if isinstance(formatted, StreamingResponse):
            raise ValueError("StreamingResponse is not supported in tuple responses")
        description = formatted.description
        new_headers: Headers = Headers(headers)
        if new_headers.contains("Content-Type"):
            headers.set("Content-Type", new_headers.get("Content-Type"))

        return Response(
            status_code=status_code,
            headers=headers,
            description=description,
        )

    def _format_response(self, res: dict | Response | StreamingResponse | bytes | tuple | str) -> Response | StreamingResponse:
        if isinstance(res, Response):
            return res

        if isinstance(res, StreamingResponse):
            return res

        if isinstance(res, dict):
            return Response(
                status_code=status_codes.HTTP_200_OK,
                headers=Headers({"Content-Type": "application/json"}),
                description=jsonify(res),
            )

        if isinstance(res, FileResponse):
            response: Response = Response(
                status_code=res.status_code,
                headers=res.headers,
                description=res.file_path,
            )
            response.file_path = res.file_path
            return response

        if isinstance(res, bytes):
            return Response(
                status_code=status_codes.HTTP_200_OK,
                headers=Headers({"Content-Type": "application/octet-stream"}),
                description=res,
            )

        if isinstance(res, tuple):
            return self._format_tuple_response(tuple(res))

        return Response(
            status_code=status_codes.HTTP_200_OK,
            headers=Headers({"Content-Type": "text/plain"}),
            description=str(res).encode("utf-8"),
        )

    def add_route(  # type: ignore
        self,
        route_type: HttpMethod,
        endpoint: str,
        handler: Callable,
        is_const: bool,
        auth_required: bool,
        openapi_name: str,
        openapi_tags: list[str],
        exception_handler: Callable | None,
        injected_dependencies: dict,
    ) -> Callable | CoroutineType:
        def wrapped_handler(*args, **kwargs):
            # In the execute functions the request is passed into *args
            request = next(filter(lambda it: isinstance(it, Request), args), None)

            handler_params = inspect.signature(handler).parameters

            if not request or (len(handler_params) == 1 and next(iter(handler_params)) is Request):
                return handler(*args, **kwargs)

            type_mapping = {
                "request": Request,
                "query_params": QueryParams,
                "headers": Headers,
                "path_params": PathParams,
                "body": Body,
                "method": Method,
                "url": Url,
                "form_data": FormData,
                "files": Files,
                "ip_addr": IPAddress,
                "identity": Identity,
            }

            type_filtered_params = {}

            for handler_param in iter(handler_params):
                for type_name in type_mapping:
                    handler_param_type = handler_params[handler_param].annotation
                    handler_param_name = handler_params[handler_param].name
                    if handler_param_type is Request:
                        type_filtered_params[handler_param_name] = request
                    elif handler_param_type is type_mapping[type_name]:
                        type_filtered_params[handler_param_name] = getattr(request, type_name)
                    elif inspect.isclass(handler_param_type):
                        if issubclass(handler_param_type, Body):
                            type_filtered_params[handler_param_name] = request.body
                        elif issubclass(handler_param_type, QueryParams):
                            type_filtered_params[handler_param_name] = request.query_params

            request_components = {
                "r": request,
                "req": request,
                "request": request,
                "query_params": request.query_params,
                "headers": request.headers,
                "path_params": request.path_params,
                "body": request.body,
                "method": request.method,
                "url": request.url,
                "ip_addr": request.ip_addr,
                "identity": request.identity,
                "form_data": request.form_data,
                "files": request.files,
                "router_dependencies": injected_dependencies["router_dependencies"],
                "global_dependencies": injected_dependencies["global_dependencies"],
                **kwargs,
            }

            name_filtered_params = {k: v for k, v in request_components.items() if k in handler_params and k not in type_filtered_params}

            filtered_params = dict(**type_filtered_params, **name_filtered_params)

            if len(filtered_params) != len(handler_params):
                invalid_args = set(handler_params) - set(filtered_params)
                raise SyntaxError(f"Unexpected request params found: {invalid_args}")

            return handler(**filtered_params)

        @wraps(handler)
        async def async_inner_handler(*args, **kwargs):
            try:
                response = self._format_response(
                    await wrapped_handler(*args, **kwargs),
                )
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(
                    exception_handler(err),
                )
            return response

        @wraps(handler)
        def inner_handler(*args, **kwargs):
            try:
                response = self._format_response(
                    wrapped_handler(*args, **kwargs),
                )
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(
                    exception_handler(err),
                )
            return response

        # these are the arguments
        params = dict(inspect.signature(handler).parameters)

        new_injected_dependencies = {}
        for dependency in injected_dependencies:
            if dependency in params:
                new_injected_dependencies[dependency] = injected_dependencies[dependency]
            else:
                _logger.debug(f"Dependency {dependency} is not used in the handler {handler.__name__}")

        if inspect.iscoroutinefunction(handler):
            function = FunctionInfo(
                async_inner_handler,
                True,
                len(params),
                params,
                new_injected_dependencies,
            )
            self.routes.append(Route(route_type, endpoint, function, is_const, auth_required, openapi_name, openapi_tags))
            return async_inner_handler
        else:
            function = FunctionInfo(
                inner_handler,
                False,
                len(params),
                params,
                new_injected_dependencies,
            )
            self.routes.append(Route(route_type, endpoint, function, is_const, auth_required, openapi_name, openapi_tags))
            return inner_handler

    def prepare_routes_openapi(self, openapi: OpenAPI, included_routers: list["SubRouter"]) -> None:
        for route in self.routes:
            openapi.add_openapi_path_obj(
                lower_http_method(route.route_type),
                route.route,
                route.openapi_name,
                route.openapi_tags,
                route.function.handler,
            )

        # TODO! after include_routes does not immediately merge all the routes
        # for router in included_routers:
        #    for route in router:
        #        openapi.add_openapi_path_obj(lower_http_method(route.route_type), route.route, route.openapi_name, route.openapi_tags, route.function.handler)

    def get_routes(self) -> list[Route]:
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self, dependencies: DependencyMap | None = None) -> None:
        super().__init__()
        self.global_middlewares: list[GlobalMiddleware] = []
        self.route_middlewares: list[RouteMiddleware] = []
        self.authentication_handler: AuthenticationHandler | None = None
        self.dependencies = DependencyMap() if dependencies is None else dependencies

    def set_authentication_handler(self, authentication_handler: AuthenticationHandler):
        self.authentication_handler = authentication_handler

    def add_route(  # type: ignore
        self,
        middleware_type: MiddlewareType,
        endpoint: str,
        route_type: HttpMethod,
        handler: Callable,
        injected_dependencies: dict,
    ) -> Callable:
        params = dict(inspect.signature(handler).parameters)

        new_injected_dependencies = {}
        for dependency in injected_dependencies:
            if dependency in params:
                new_injected_dependencies[dependency] = injected_dependencies[dependency]
            else:
                _logger.debug(f"Dependency {dependency} is not used in the middleware handler {handler.__name__}")

        function = FunctionInfo(
            handler,
            inspect.iscoroutinefunction(handler),
            len(params),
            params,
            new_injected_dependencies,
        )
        self.route_middlewares.append(RouteMiddleware(middleware_type, endpoint, function, route_type))
        return handler

    def add_auth_middleware(self, endpoint: str, route_type: HttpMethod):
        """
        This method adds an authentication middleware to the specified endpoint.
        """

        injected_dependencies: dict = {}

        def decorator(handler):
            @wraps(handler)
            def inner_handler(request: Request, *args):
                if not self.authentication_handler:
                    raise AuthenticationNotConfiguredError()
                identity = self.authentication_handler.authenticate(request)
                if identity is None:
                    return self.authentication_handler.unauthorized_response
                request.identity = identity

                return request

            self.add_route(
                MiddlewareType.BEFORE_REQUEST,
                endpoint,
                route_type,
                inner_handler,
                injected_dependencies,
            )
            return inner_handler

        return decorator

    # These inner functions are basically a wrapper around the closure(decorator) being returned.
    # They take a handler, convert it into a closure and return the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_middleware(self, middleware_type: MiddlewareType, endpoint: str | None = None) -> Callable[..., None]:
        """
        This method adds a middleware to the router.

        Rules:
            If endpoint is None, the middleware is added as a global middleware.
            If endpoint is provided, the middleware is added to that specific endpoint.
            Only None is supported for global middleware, empty string is not supported.
            empty string or "/" is considered as root endpoint.

        Args:
            middleware_type: The type of middleware to add (before_request, after_request).
            endpoint: The endpoint to add the middleware to. If None, the middleware is added as a global middleware.

        Returns:
            A decorator that takes a handler and adds it as a middleware.
        """
        # no dependency injection here
        injected_dependencies: dict = {}

        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args, **kwargs):
                return await handler(*args, **kwargs)

            @wraps(handler)
            def inner_handler(*args, **kwargs):
                return handler(*args, **kwargs)

            if endpoint is not None:
                if inspect.iscoroutinefunction(handler):
                    self.add_route(
                        middleware_type,
                        endpoint,
                        HttpMethod.GET,
                        async_inner_handler,
                        injected_dependencies,
                    )
                else:
                    self.add_route(middleware_type, endpoint, HttpMethod.GET, inner_handler, injected_dependencies)
            else:
                params = dict(inspect.signature(handler).parameters)

                if inspect.iscoroutinefunction(handler):
                    self.global_middlewares.append(
                        GlobalMiddleware(
                            middleware_type,
                            FunctionInfo(
                                async_inner_handler,
                                True,
                                len(params),
                                params,
                                injected_dependencies,
                            ),
                        )
                    )
                else:
                    self.global_middlewares.append(
                        GlobalMiddleware(
                            middleware_type,
                            FunctionInfo(
                                inner_handler,
                                False,
                                len(params),
                                params,
                                injected_dependencies,
                            ),
                        )
                    )

        return inner

    def get_route_middlewares(self) -> list[RouteMiddleware]:
        return self.route_middlewares

    def get_global_middlewares(self) -> list[GlobalMiddleware]:
        return self.global_middlewares


class WebSocketRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes: dict = {}

    def add_route(self, endpoint: str, web_socket: WebSocket) -> None:  # type: ignore
        self.routes[endpoint] = web_socket

    def get_routes(self) -> dict[str, WebSocket]:
        return self.routes
