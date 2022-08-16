from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from inspect import signature


class BaseRouter(ABC):
    @abstractmethod
    def add_route(*args):
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

    def add_route(self, route_type, endpoint, handler, const):
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

    def get_routes(self):
        return self.routes


class MiddlewareRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = []

    def add_route(self, route_type, endpoint, handler):
        number_of_params = len(signature(handler).parameters)
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
    def add_after_request(self, endpoint):
        def inner(handler):
            async def async_inner_handler(*args):
                await handler(*args)
                return args

            def inner_handler(*args):
                handler(*args)
                return args

            if iscoroutinefunction(handler):
                self.add_route("AFTER_REQUEST", endpoint, async_inner_handler)
            else:
                self.add_route("AFTER_REQUEST", endpoint, inner_handler)

        return inner

    def add_before_request(self, endpoint):
        def inner(handler):
            async def async_inner_handler(*args):
                await handler(*args)
                return args

            def inner_handler(*args):
                handler(*args)
                return args

            if iscoroutinefunction(handler):
                self.add_route("BEFORE_REQUEST", endpoint, async_inner_handler)
            else:
                self.add_route("BEFORE_REQUEST", endpoint, inner_handler)

        return inner

    def get_routes(self):
        return self.routes


class WebSocketRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()
        self.routes = {}

    def add_route(self, endpoint, web_socket):
        self.routes[endpoint] = web_socket

    def get_routes(self):
        return self.routes
