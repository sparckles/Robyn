import inspect
from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from functools import wraps
from inspect import signature
from types import CoroutineType
from typing import Callable, Dict, List, NamedTuple, Union, Optional
from robyn.authentication import AuthenticationHandler, AuthenticationNotConfiguredError
from robyn.dependency_injection import DependencyMap
from robyn.responses import FileResponse

from robyn.robyn import (
    FunctionInfo,
    Headers,
    HttpMethod,
    MiddlewareType,
    Request,
    Response,
)
from robyn import status_codes
from robyn.jsonify import jsonify

from robyn.ws import WebSocket

import logging

_logger = logging.getLogger(__name__)


class Route(NamedTuple):
    route_type: HttpMethod
    route: str
    function: FunctionInfo
    is_const: bool


class RouteMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    route: str
    function: FunctionInfo


class GlobalMiddleware(NamedTuple):
    middleware_type: MiddlewareType
    function: FunctionInfo


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args) -> Union[Callable, CoroutineType, WebSocket]: ...


class Router(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes: List[Route] = []

    def _format_response(
        self,
        res: Union[Dict, Response, bytes, tuple, str],
    ) -> Response:
        headers = Headers({"Content-Type": "text/plain"})

        response = {}
        if isinstance(res, dict):
            # this should change
            headers = Headers({})
            if "Content-Type" not in headers:
                headers.set("Content-Type", "text/json")

            description = jsonify(res)

            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers=headers,
                description=description,
            )
        elif isinstance(res, Response):
            response = res
        elif isinstance(res, FileResponse):
            response = Response(
                status_code=res.status_code,
                headers=res.headers,
                description=res.file_path,
            )
            response.file_path = res.file_path

        elif isinstance(res, bytes):
            headers = Headers({"Content-Type": "application/octet-stream"})
            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers=headers,
                description=res,
            )
        elif isinstance(res, tuple):
            if len(res) != 3:
                raise ValueError("Tuple should have 3 elements")
            else:
                description, headers, status_code = res
                description = self._format_response(description).description
                new_headers = Headers(headers)
                if "Content-Type" in new_headers:
                    headers.set("Content-Type", new_headers.get("Content-Type"))

                response = Response(
                    status_code=status_code,
                    headers=headers,
                    description=description,
                )
        else:
            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers=headers,
                description=str(res).encode("utf-8"),
            )
        return response

    def add_route(
        self,
        route_type: HttpMethod,
        endpoint: str,
        handler: Callable,
        is_const: bool,
        exception_handler: Optional[Callable],
        injected_dependencies: dict,
    ) -> Union[Callable, CoroutineType]:
        @wraps(handler)
        async def async_inner_handler(*args, **kwargs):
            try:
                response = self._format_response(
                    await handler(*args, **kwargs),
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
                    handler(*args, **kwargs),
                )
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(
                    exception_handler(err),
                )
            return response

        number_of_params = len(signature(handler).parameters)
        # these are the arguments
        params = dict(inspect.signature(handler).parameters)

        new_injected_dependencies = {}
        for dependency in injected_dependencies:
            if dependency in params:
                new_injected_dependencies[dependency] = injected_dependencies[dependency]
            else:
                _logger.debug(f"Dependency {dependency} is not used in the handler {handler.__name__}")

        if iscoroutinefunction(handler):
            function = FunctionInfo(
                async_inner_handler,
                True,
                number_of_params,
                params,
                new_injected_dependencies,
            )
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return async_inner_handler
        else:
            function = FunctionInfo(
                inner_handler,
                False,
                number_of_params,
                params,
                new_injected_dependencies,
            )
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return inner_handler

    def get_routes(self) -> List[Route]:
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self, dependencies: DependencyMap = DependencyMap()) -> None:
        super().__init__()
        self.global_middlewares: List[GlobalMiddleware] = []
        self.route_middlewares: List[RouteMiddleware] = []
        self.authentication_handler: Optional[AuthenticationHandler] = None
        self.dependencies = dependencies

    def set_authentication_handler(self, authentication_handler: AuthenticationHandler):
        self.authentication_handler = authentication_handler

    def add_route(
        self,
        middleware_type: MiddlewareType,
        endpoint: str,
        handler: Callable,
        injected_dependencies: dict,
    ) -> Callable:
        params = dict(inspect.signature(handler).parameters)
        number_of_params = len(params)

        new_injected_dependencies = {}
        for dependency in injected_dependencies:
            if dependency in params:
                new_injected_dependencies[dependency] = injected_dependencies[dependency]
            else:
                _logger.debug(f"Dependency {dependency} is not used in the middleware handler {handler.__name__}")

        function = FunctionInfo(
            handler,
            iscoroutinefunction(handler),
            number_of_params,
            params,
            new_injected_dependencies,
        )
        self.route_middlewares.append(RouteMiddleware(middleware_type, endpoint, function))
        return handler

    def add_auth_middleware(self, endpoint: str):
        """
        This method adds an authentication middleware to the specified endpoint.
        """

        injected_dependencies = {}

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
                inner_handler,
                injected_dependencies,
            )
            return inner_handler

        return decorator

    # These inner functions are basically a wrapper around the closure(decorator) being returned.
    # They take a handler, convert it into a closure and return the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_middleware(self, middleware_type: MiddlewareType, endpoint: Optional[str]) -> Callable[..., None]:
        # no dependency injection here
        injected_dependencies = {}

        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args, **kwargs):
                return await handler(*args, **kwargs)

            @wraps(handler)
            def inner_handler(*args, **kwargs):
                return handler(*args, **kwargs)

            if endpoint is not None:
                if iscoroutinefunction(handler):
                    self.add_route(
                        middleware_type,
                        endpoint,
                        async_inner_handler,
                        injected_dependencies,
                    )
                else:
                    self.add_route(middleware_type, endpoint, inner_handler, injected_dependencies)
            else:
                params = dict(inspect.signature(handler).parameters)

                if iscoroutinefunction(handler):
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

    def get_route_middlewares(self) -> List[RouteMiddleware]:
        return self.route_middlewares

    def get_global_middlewares(self) -> List[GlobalMiddleware]:
        return self.global_middlewares


class WebSocketRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = {}

    def add_route(self, endpoint: str, web_socket: WebSocket) -> None:
        self.routes[endpoint] = web_socket

    def get_routes(self) -> Dict[str, WebSocket]:
        return self.routes
