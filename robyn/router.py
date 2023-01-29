from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from functools import wraps
from inspect import signature
from types import CoroutineType
from typing import Callable, Dict, List, Tuple, Union

from robyn.robyn import FunctionInfo, Response
from robyn.ws import WS

Route = Tuple[str, str, FunctionInfo, bool]
MiddlewareRoute = Tuple[str, str, FunctionInfo]


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args) -> Union[Callable, CoroutineType, WS]:
        ...


class Router(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = []

    def _format_response(self, res):
        response = {}
        if type(res) == dict:
            status_code = res.get("status_code", 200)
            headers = res.get("headers", {"Content-Type": "text/plain"})
            body = res.get("body", "")

            if type(status_code) != int:
                status_code = int(status_code)  # status_code can potentially be string

            response = Response(status_code=status_code, headers=headers, body=body)
            file_path = res.get("file_path")
            if file_path is not None:
                response.set_file_path(file_path)
        elif type(res) == Response:
            response = res
        elif type(res) == bytes:
            response = Response(
                status_code=200,
                headers={"Content-Type": "application/octet-stream"},
                body=res,
            )
        else:
            response = Response(
                status_code=200,
                headers={"Content-Type": "text/plain"},
                body=str(res).encode("utf-8"),
            )
        return response

    def add_route(
        self, route_type: str, endpoint: str, handler: Callable, is_const: bool
    ) -> Union[Callable, CoroutineType]:
        @wraps(handler)
        async def async_inner_handler(*args):
            response = self._format_response(await handler(*args))
            return response

        @wraps(handler)
        def inner_handler(*args):
            response = self._format_response(handler(*args))
            return response

        number_of_params = len(signature(handler).parameters)
        if iscoroutinefunction(handler):
            function = FunctionInfo(async_inner_handler, True, number_of_params)
            self.routes.append((route_type, endpoint, function, is_const))
            return async_inner_handler
        else:
            function = FunctionInfo(inner_handler, False, number_of_params)
            self.routes.append((route_type, endpoint, function, is_const))
            return inner_handler

    def get_routes(self) -> List[Route]:
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = []

    def add_route(self, route_type: str, endpoint: str, handler: Callable) -> Callable:
        number_of_params = len(signature(handler).parameters)
        function = FunctionInfo(handler, iscoroutinefunction(handler), number_of_params)
        self.routes.append((route_type, endpoint, function))
        return handler

    # These inner function is basically a wrapper arround the closure(decorator)
    # being returned.
    # It takes in a handler and converts it in into a closure
    # and returns the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_after_request(self, endpoint: str) -> Callable[..., None]:
        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args):
                await handler(*args)
                return args

            @wraps(handler)
            def inner_handler(*args):
                handler(*args)
                return args

            if iscoroutinefunction(handler):
                self.add_route("AFTER_REQUEST", endpoint, async_inner_handler)
            else:
                self.add_route("AFTER_REQUEST", endpoint, inner_handler)

        return inner

    def add_before_request(self, endpoint: str) -> Callable[..., None]:
        def inner(handler):
            @wraps(handler)
            async def async_inner_handler(*args):
                await handler(*args)
                return args

            @wraps(handler)
            def inner_handler(*args):
                handler(*args)
                return args

            if iscoroutinefunction(handler):
                self.add_route("BEFORE_REQUEST", endpoint, async_inner_handler)
            else:
                self.add_route("BEFORE_REQUEST", endpoint, inner_handler)

        return inner

    def get_routes(self) -> List[MiddlewareRoute]:
        return self.routes


class WebSocketRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = {}

    def add_route(self, endpoint: str, web_socket: WS) -> None:
        self.routes[endpoint] = web_socket

    def get_routes(self) -> Dict[str, WS]:
        return self.routes
