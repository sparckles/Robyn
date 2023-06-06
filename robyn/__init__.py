import asyncio
import logging
import multiprocess as mp
import os
from typing import Callable, List, Optional, Tuple
from nestd import get_all_nested

from robyn.argument_parser import Config
from robyn.logger import Colors
from robyn.reloader import setup_reloader
from robyn.env_populator import load_vars
from robyn.events import Events
from robyn.logger import logger
from robyn.processpool import run_processes
from robyn.responses import jsonify, serve_file, serve_html
from robyn.robyn import FunctionInfo, HttpMethod, Request, Response, get_version
from robyn.router import MiddlewareRouter, MiddlewareType, Router, WebSocketRouter
from robyn.types import Directory, Header
from robyn import status_codes
from robyn.ws import WS


__version__ = get_version()


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object: str, config: Config = Config()) -> None:
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.config = config

        load_vars(project_root=directory_path)
        logging.basicConfig(level=self.config.log_level)

        if self.config.log_level.lower() != "warn":
            logger.info(
                "SERVER IS RUNNING IN VERBOSE/DEBUG MODE. Set --log-level to WARN to run in production mode.",
                Colors.BLUE,
            )
        # If we are in dev mode, we need to setup the reloader
        # This process will be used by the watchdog observer while running the actual server as children processes
        if self.config.dev and not os.environ.get("IS_RELOADER_RUNNING", False):
            setup_reloader(self.directory_path, self.file_path)
            exit(0)

        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.request_headers: List[Header] = []  # This needs a better type
        self.response_headers: List[Header] = []  # This needs a better type
        self.directories: List[Directory] = []
        self.event_handlers = {}
        self.exception_handler: Optional[Callable] = None

    def _add_route(
        self, route_type: HttpMethod, endpoint: str, handler: Callable, is_const=False
    ):
        """
        This is base handler for all the decorators

        :param route_type str: route type between GET/POST/PUT/DELETE/PATCH
        :param endpoint str: endpoint for the route added
        :param handler function: represents the sync or async function passed as a handler for the route
        """

        """ We will add the status code here only
        """
        return self.router.add_route(
            route_type, endpoint, handler, is_const, self.exception_handler
        )

    def before_request(self, endpoint: Optional[str] = None) -> Callable[..., None]:
        """
        You can use the @app.before_request decorator to call a method before routing to the specified endpoint

        :param endpoint str: endpoint to server the route
        """

        return self.middleware_router.add_middleware(
            MiddlewareType.BEFORE_REQUEST, endpoint
        )

    def after_request(self, endpoint: Optional[str] = None) -> Callable[..., None]:
        """
        You can use the @app.after_request decorator to call a method after routing to the specified endpoint

        :param endpoint str: endpoint to server the route
        """

        return self.middleware_router.add_middleware(
            MiddlewareType.AFTER_REQUEST, endpoint
        )

    def add_directory(
        self,
        route: str,
        directory_path: str,
        index_file: Optional[str] = None,
        show_files_listing: bool = False,
    ):
        self.directories.append(
            Directory(route, directory_path, show_files_listing, index_file)
        )

    def add_request_header(self, key: str, value: str) -> None:
        self.request_headers.append(Header(key, value))

    def add_response_header(self, key: str, value: str) -> None:
        self.response_headers.append(Header(key, value))

    def add_web_socket(self, endpoint: str, ws: WS) -> None:
        self.web_socket_router.add_route(endpoint, ws)

    def _add_event_handler(self, event_type: Events, handler: Callable) -> None:
        logger.info(f"Add event {event_type} handler")
        if event_type not in {Events.STARTUP, Events.SHUTDOWN}:
            return

        is_async = asyncio.iscoroutinefunction(handler)
        self.event_handlers[event_type] = FunctionInfo(handler, is_async, 0)

    def startup_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.STARTUP, handler)

    def shutdown_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.SHUTDOWN, handler)

    def start(self, url: str = "127.0.0.1", port: int = 8080):
        """
        Starts the server

        :param port int: represents the port number at which the server is listening
        """

        url = os.getenv("ROBYN_URL", url)
        port = int(os.getenv("ROBYN_PORT", port))

        logger.info(f"Robyn version: {__version__}")
        logger.info(f"Starting server at {url}:{port}")

        mp.allow_connection_pickling()

        run_processes(
            url,
            port,
            self.directories,
            self.request_headers,
            self.router.get_routes(),
            self.middleware_router.get_global_middlewares(),
            self.middleware_router.get_route_middlewares(),
            self.web_socket_router.get_routes(),
            self.event_handlers,
            self.config.workers,
            self.config.processes,
            self.response_headers,
        )

    def exception(self, exception_handler: Callable):
        self.exception_handler = exception_handler

    def add_view(self, endpoint: str, view: Callable, const: bool = False):
        """
        This is base handler for the view decorators

        :param endpoint str: endpoint for the route added
        :param handler function: represents the function passed as a parent handler for single route with different route types
        """
        http_methods = {
            "GET": HttpMethod.GET,
            "POST": HttpMethod.POST,
            "PUT": HttpMethod.PUT,
            "DELETE": HttpMethod.DELETE,
            "PATCH": HttpMethod.PATCH,
            "HEAD": HttpMethod.HEAD,
            "OPTIONS": HttpMethod.OPTIONS,
        }

        def get_functions(view) -> List[Tuple[HttpMethod, Callable]]:
            functions = get_all_nested(view)
            output = []
            for name, handler in functions:
                route_type = name.upper()
                method = http_methods.get(route_type)
                if method is not None:
                    output.append((method, handler))
            return output

        handlers = get_functions(view)
        for route_type, handler in handlers:
            self._add_route(route_type, endpoint, handler, const)

    def view(self, endpoint: str, const: bool = False):
        """
        The @app.view decorator to add a view with the GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_view(endpoint, handler, const)

        return inner

    def get(self, endpoint: str, const: bool = False):
        """
        The @app.get decorator to add a route with the GET method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.GET, endpoint, handler, const)

        return inner

    def post(self, endpoint: str):
        """
        The @app.post decorator to add a route with POST method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.POST, endpoint, handler)

        return inner

    def put(self, endpoint: str):
        """
        The @app.put decorator to add a get route with PUT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.PUT, endpoint, handler)

        return inner

    def delete(self, endpoint: str):
        """
        The @app.delete decorator to add a route with DELETE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.DELETE, endpoint, handler)

        return inner

    def patch(self, endpoint: str):
        """
        The @app.patch decorator to add a route with PATCH method

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            return self._add_route(HttpMethod.PATCH, endpoint, handler)

        return inner

    def head(self, endpoint: str):
        """
        The @app.head decorator to add a route with HEAD method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.HEAD, endpoint, handler)

        return inner

    def options(self, endpoint: str):
        """
        The @app.options decorator to add a route with OPTIONS method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.OPTIONS, endpoint, handler)

        return inner

    def connect(self, endpoint: str):
        """
        The @app.connect decorator to add a route with CONNECT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.CONNECT, endpoint, handler)

        return inner

    def trace(self, endpoint: str):
        """
        The @app.trace decorator to add a route with TRACE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route(HttpMethod.TRACE, endpoint, handler)

        return inner

    def include_router(self, router):
        """
        The method to include the routes from another router

        :param router Robyn: the router object to include the routes from
        """
        self.router.routes.extend(router.router.routes)
        self.middleware_router.global_middlewares.extend(
            router.middleware_router.global_middlewares
        )
        self.middleware_router.route_middlewares.extend(
            router.middleware_router.route_middlewares
        )

        # extend the websocket routes
        prefix = router.prefix
        for route in router.web_socket_router.routes:
            new_endpoint = f"{prefix}{route}"
            self.web_socket_router.routes[
                new_endpoint
            ] = router.web_socket_router.routes[route]


class SubRouter(Robyn):
    def __init__(
        self, file_object: str, prefix: str = "", config: Config = Config()
    ) -> None:
        super().__init__(file_object, config)
        self.prefix = prefix

    def __add_prefix(self, endpoint: str):
        return f"{self.prefix}{endpoint}"

    def get(self, endpoint: str, const: bool = False):
        return super().get(self.__add_prefix(endpoint), const)

    def post(self, endpoint: str):
        return super().post(self.__add_prefix(endpoint))

    def put(self, endpoint: str):
        return super().put(self.__add_prefix(endpoint))

    def delete(self, endpoint: str):
        return super().delete(self.__add_prefix(endpoint))

    def patch(self, endpoint: str):
        return super().patch(self.__add_prefix(endpoint))

    def head(self, endpoint: str):
        return super().head(self.__add_prefix(endpoint))

    def trace(self, endpoint: str):
        return super().trace(self.__add_prefix(endpoint))

    def options(self, endpoint: str):
        return super().options(self.__add_prefix(endpoint))


def ALLOW_CORS(app: Robyn, origins: List[str]):
    """Allows CORS for the given origins for the entire router."""
    for origin in origins:
        app.add_request_header("Access-Control-Allow-Origin", origin)
        app.add_request_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS",
        )
        app.add_request_header(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        app.add_request_header("Access-Control-Allow-Credentials", "true")


__all__ = [
    "Robyn",
    "Request",
    "Response",
    "status_codes",
    "jsonify",
    "serve_file",
    "serve_html",
    "ALLOW_CORS",
]
