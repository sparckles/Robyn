from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from inspect import signature
from typing import Callable, Dict, List, Tuple

from robyn.ws import WS

Route = Tuple[str, str, Callable, bool, int, bool]
MiddlewareRoute = Tuple[str, str, Callable, bool, int]


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args) -> None:
        ...


class Router(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = []

    def _format_response(self, res):
        # handle file handlers
        response = {}
        if type(res) == dict:
            if "status_code" not in res:
                res["status_code"] = "200"
                response = res
            else:
                if type(res["status_code"]) == int:
                    res["status_code"] = str(res["status_code"])

                response = {
                    "status_code": "200",
                    "body": res["body"],
                    **res
                }
        else:
            response = {"status_code": "200", "body": res, "type": "text"}

        return response

    def add_route(self, route_type: str, endpoint: str, handler: Callable, const: bool) -> None:
        async def async_inner_handler(*args):
            response = self._format_response(await handler(*args))
            return response

        def inner_handler(*args):
            response = self._format_response(handler(*args))
            return response

        number_of_params = len(signature(handler).parameters)
        if iscoroutinefunction(handler):
            self.routes.append(
                (
                    route_type,
                    endpoint,
                    async_inner_handler,
                    True,
                    number_of_params,
                    const
                )
            )
        else:
            self.routes.append(
                (
                    route_type,
                    endpoint,
                    inner_handler,
                    False,
                    number_of_params,
                    const
                )
            )

    def get_routes(self) -> List[Route]:
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = []

    def add_route(self, route_type: str, endpoint: str, handler: Callable, number_of_params=0) -> None:
        print(route_type, handler, signature(handler).parameters, number_of_params)
        self.routes.append(
            (
                route_type,
                endpoint,
                handler,
                iscoroutinefunction(handler),
                number_of_params,
            )
        )

    # These inner function is basically a wrapper arround the closure(decorator)
    # being returned.
    # It takes in a handler and converts it in into a closure
    # and returns the arguments.
    # Arguments are returned as they could be modified by the middlewares.
    def add_after_request(self, endpoint: str) -> Callable[..., None]:
        def inner(handler): # number_of_params 

            async def async_inner_handler(*args):
                await handler(*args)
                return args

            def inner_handler(*args):
                handler(*args)
                return args

            number_of_params = len(signature(handler).parameters)


            if iscoroutinefunction(handler):
                self.add_route("AFTER_REQUEST", endpoint, async_inner_handler, number_of_params)
            else:
                self.add_route("AFTER_REQUEST", endpoint, inner_handler, number_of_params)

        return inner

    def add_before_request(self, endpoint: str) -> Callable[..., None]:
        def inner(handler):
            async def async_inner_handler(*args):
                await handler(*args)
                return args

            def inner_handler(*args):
                handler(*args)
                return args

            number_of_params = len(signature(handler).parameters)

            if iscoroutinefunction(handler):
                self.add_route("BEFORE_REQUEST", endpoint, async_inner_handler, number_of_params)
            else:
                self.add_route("BEFORE_REQUEST", endpoint, inner_handler, number_of_params)

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
