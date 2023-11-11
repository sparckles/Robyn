from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from functools import wraps
from inspect import signature
from types import CoroutineType
from typing import Callable, Dict, List, NamedTuple, Union, Optional
from robyn.authentication import AuthenticationHandler, AuthenticationNotConfiguredError

from robyn.robyn import FunctionInfo, HttpMethod, MiddlewareType, Request, Response
from robyn import status_codes

from robyn.ws import WebSocket
from robyn.types import Header


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
    def add_route(*args) -> Union[Callable, CoroutineType, WebSocket]:
        ...


class Router(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes: List[Route] = []

    def _format_response(
        self,
        res: dict,
        default_response_header: dict,
    ) -> Response:
        headers = {"Content-Type": "text/plain"} if not default_response_header else default_response_header
        response = {}
        if isinstance(res, dict):
            status_code = res.get("status_code", status_codes.HTTP_200_OK)
            headers = res.get("headers", headers)
            description = res.get("description", "")

            if not isinstance(status_code, int):
                status_code = int(status_code)  # status_code can potentially be string

            response = Response(status_code=status_code, headers=headers, description=description)
            file_path = res.get("file_path")
            if file_path is not None:
                response.file_path = file_path
        elif isinstance(res, Response):
            response = res
        elif isinstance(res, bytes):
            response = Response(
                status_code=status_codes.HTTP_200_OK,
                headers={"Content-Type": "application/octet-stream"},
                description=res,
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
        default_response_headers: List[Header],
    ) -> Union[Callable, CoroutineType]:
        response_headers = {d.key: d.val for d in default_response_headers}

        @wraps(handler)
        async def async_inner_handler(*args):
            try:
                response = self._format_response(
                    await handler(*args),
                    response_headers,
                )
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(
                    exception_handler(err),
                    response_headers,
                )
            return response

        @wraps(handler)
        def inner_handler(*args):
            try:
                response = self._format_response(
                    handler(*args),
                    response_headers,
                )
            except Exception as err:
                if exception_handler is None:
                    raise
                response = self._format_response(
                    exception_handler(err),
                    response_headers,
                )
            return response

        number_of_params = len(signature(handler).parameters)
        if iscoroutinefunction(handler):
            function = FunctionInfo(async_inner_handler, True, number_of_params)
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return async_inner_handler
        else:
            function = FunctionInfo(inner_handler, False, number_of_params)
            self.routes.append(Route(route_type, endpoint, function, is_const))
            return inner_handler

    def get_routes(self) -> List[Route]:
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.global_middlewares: List[GlobalMiddleware] = []
        self.route_middlewares: List[RouteMiddleware] = []
        self.authentication_handler: Optional[AuthenticationHandler] = None

    def set_authentication_handler(self, authentication_handler: AuthenticationHandler):
        self.authentication_handler = authentication_handler

    def add_route(self, middleware_type: MiddlewareType, endpoint: str, handler: Callable) -> Callable:
        number_of_params = len(signature(handler).parameters)
        function = FunctionInfo(handler, iscoroutinefunction(handler), number_of_params)
        self.route_middlewares.append(RouteMiddleware(middleware_type, endpoint, function))
        return handler

    def add_auth_middleware(self, endpoint: str):
        """
        This method adds an authentication middleware to the specified endpoint.
        """

        def inner(handler):
            def inner_handler(request: Request, *args):
                if not self.authentication_handler:
                    raise AuthenticationNotConfiguredError()
                identity = self.authentication_handler.authenticate(request)
                if identity is None:
                    return self.authentication_handler.unauthorized_response
                request.identity = identity
                return request

            self.add_route(MiddlewareType.BEFORE_REQUEST, endpoint, inner_handler)
            return inner_handler

        return inner

    # These inner functions are basically a wrapper around the closure(decorator) being returned.
    # They take a handler, convert it into a closure and return the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_middleware(self, middleware_type: MiddlewareType, endpoint: Optional[str]) -> Callable[..., None]:
        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args):
                return await handler(*args)

            @wraps(handler)
            def inner_handler(*args):
                return handler(*args)

            if endpoint is not None:
                if iscoroutinefunction(handler):
                    self.add_route(middleware_type, endpoint, async_inner_handler)
                else:
                    self.add_route(middleware_type, endpoint, inner_handler)
            else:
                if iscoroutinefunction(handler):
                    self.global_middlewares.append(
                        GlobalMiddleware(
                            middleware_type,
                            FunctionInfo(
                                async_inner_handler,
                                True,
                                len(signature(async_inner_handler).parameters),
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
                                len(signature(inner_handler).parameters),
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
