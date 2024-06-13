import asyncio
import logging
import os
import socket
from typing import Callable, List, Optional, Tuple, Union

import multiprocess as mp
from nestd import get_all_nested

from robyn import status_codes
from robyn.argument_parser import Config
from robyn.authentication import AuthenticationHandler
from robyn.dependency_injection import DependencyMap
from robyn.env_populator import load_vars
from robyn.events import Events
from robyn.jsonify import jsonify
from robyn.logger import Colors, logger
from robyn.processpool import run_processes
from robyn.reloader import compile_rust_files
from robyn.responses import html, serve_file, serve_html
from robyn.robyn import FunctionInfo, Headers, HttpMethod, Request, Response, WebSocketConnector, get_version
from robyn.router import MiddlewareRouter, MiddlewareType, Router, WebSocketRouter
from robyn.types import Directory
from robyn.ws import WebSocket

__version__ = get_version()


config = Config()

if (compile_path := config.compile_rust_path) is not None:
    compile_rust_files(compile_path)
    print("Compiled rust files")


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(
        self,
        file_object: str,
        config: Config = Config(),
        dependencies: DependencyMap = DependencyMap(),
    ) -> None:
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.config = config
        self.dependencies = dependencies

        load_vars(project_root=directory_path)
        logging.basicConfig(level=self.config.log_level)

        if self.config.log_level.lower() != "warn":
            logger.info(
                "SERVER IS RUNNING IN VERBOSE/DEBUG MODE. Set --log-level to WARN to run in production mode.",
                color=Colors.BLUE,
            )
        if self.config.dev:
            exit("Dev mode is not supported in the python wrapper. Please use the CLI. e.g. python3 -m robyn app.py --dev ")

        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.request_headers: Headers = Headers({})
        self.response_headers: Headers = Headers({})
        self.directories: List[Directory] = []
        self.event_handlers = {}
        self.exception_handler: Optional[Callable] = None
        self.authentication_handler: Optional[AuthenticationHandler] = None

    def add_route(
        self,
        route_type: Union[HttpMethod, str],
        endpoint: str,
        handler: Callable,
        is_const: bool = False,
        auth_required: bool = False,
    ):
        """
        Connect a URI to a handler

        :param route_type str: route type between GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/TRACE
        :param endpoint str: endpoint for the route added
        :param handler function: represents the sync or async function passed as a handler for the route
        :param is_const bool: represents if the handler is a const function or not
        :param auth_required bool: represents if the route needs authentication or not
        """

        """ We will add the status code here only
        """
        injected_dependencies = self.dependencies.get_dependency_map(self)

        if auth_required:
            self.middleware_router.add_auth_middleware(endpoint)(handler)

        if isinstance(route_type, str):
            http_methods = {
                "GET": HttpMethod.GET,
                "POST": HttpMethod.POST,
                "PUT": HttpMethod.PUT,
                "DELETE": HttpMethod.DELETE,
                "PATCH": HttpMethod.PATCH,
                "HEAD": HttpMethod.HEAD,
                "OPTIONS": HttpMethod.OPTIONS,
            }
            route_type = http_methods[route_type]

        add_route_response = self.router.add_route(
            route_type=route_type,
            endpoint=endpoint,
            handler=handler,
            is_const=is_const,
            exception_handler=self.exception_handler,
            injected_dependencies=injected_dependencies,
        )

        logger.info("Added route %s %s", route_type, endpoint)

        return add_route_response

    def inject(self, **kwargs):
        """
        Injects the dependencies for the route

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_router_dependency(self, **kwargs)

    def inject_global(self, **kwargs):
        """
        Injects the dependencies for the global routes
        Ideally, this function should be a global function

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_global_dependency(**kwargs)

    def before_request(self, endpoint: Optional[str] = None) -> Callable[..., None]:
        """
        You can use the @app.before_request decorator to call a method before routing to the specified endpoint

        :param endpoint str|None: endpoint to server the route. If None, the middleware will be applied to all the routes.
        """

        return self.middleware_router.add_middleware(MiddlewareType.BEFORE_REQUEST, endpoint)

    def after_request(self, endpoint: Optional[str] = None) -> Callable[..., None]:
        """
        You can use the @app.after_request decorator to call a method after routing to the specified endpoint

        :param endpoint str|None: endpoint to server the route. If None, the middleware will be applied to all the routes.
        """
        return self.middleware_router.add_middleware(MiddlewareType.AFTER_REQUEST, endpoint)

    def add_directory(
        self,
        route: str,
        directory_path: str,
        index_file: Optional[str] = None,
        show_files_listing: bool = False,
    ):
        self.directories.append(Directory(route, directory_path, show_files_listing, index_file))

    def add_request_header(self, key: str, value: str) -> None:
        self.request_headers.append(key, value)

    def add_response_header(self, key: str, value: str) -> None:
        self.response_headers.append(key, value)

    def set_request_header(self, key: str, value: str) -> None:
        self.request_headers.set(key, value)

    def set_response_header(self, key: str, value: str) -> None:
        self.response_headers.set(key, value)

    def add_web_socket(self, endpoint: str, ws: WebSocket) -> None:
        self.web_socket_router.add_route(endpoint, ws)

    def _add_event_handler(self, event_type: Events, handler: Callable) -> None:
        logger.info("Added event %s handler", event_type)
        if event_type not in {Events.STARTUP, Events.SHUTDOWN}:
            return

        is_async = asyncio.iscoroutinefunction(handler)
        self.event_handlers[event_type] = FunctionInfo(handler, is_async, 0, {}, {})

    def startup_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.STARTUP, handler)

    def shutdown_handler(self, handler: Callable) -> None:
        self._add_event_handler(Events.SHUTDOWN, handler)

    def is_port_in_use(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            raise Exception(f"Invalid port number: {port}")

    def start(self, host: str = "127.0.0.1", port: int = 8080, _check_port: bool = True):
        """
        Starts the server

        :param host str: represents the host at which the server is listening
        :param port int: represents the port number at which the server is listening
        :param _check_port bool: represents if the port should be checked if it is already in use
        """

        host = os.getenv("ROBYN_HOST", host)
        port = int(os.getenv("ROBYN_PORT", port))
        open_browser = bool(os.getenv("ROBYN_BROWSER_OPEN", self.config.open_browser))

        if _check_port:
            while self.is_port_in_use(port):
                logger.error("Port %s is already in use. Please use a different port.", port)
                try:
                    port = int(input("Enter a different port: "))
                except Exception:
                    logger.error("Invalid port number. Please enter a valid port number.")
                    continue

        logger.info("Robyn version: %s", __version__)
        logger.info("Starting server at http://%s:%s", host, port)

        mp.allow_connection_pickling()

        run_processes(
            host,
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
            open_browser,
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
            self.add_route(route_type, endpoint, handler, const)

    def view(self, endpoint: str, const: bool = False):
        """
        The @app.view decorator to add a view with the GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_view(endpoint, handler, const)

        return inner

    def get(self, endpoint: str, const: bool = False, auth_required: bool = False):
        """
        The @app.get decorator to add a route with the GET method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.GET, endpoint, handler, const, auth_required)

        return inner

    def post(self, endpoint: str, auth_required: bool = False):
        """
        The @app.post decorator to add a route with POST method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.POST, endpoint, handler, auth_required=auth_required)

        return inner

    def put(self, endpoint: str, auth_required: bool = False):
        """
        The @app.put decorator to add a get route with PUT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.PUT, endpoint, handler, auth_required=auth_required)

        return inner

    def delete(self, endpoint: str, auth_required: bool = False):
        """
        The @app.delete decorator to add a route with DELETE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.DELETE, endpoint, handler, auth_required=auth_required)

        return inner

    def patch(self, endpoint: str, auth_required: bool = False):
        """
        The @app.patch decorator to add a route with PATCH method

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            return self.add_route(HttpMethod.PATCH, endpoint, handler, auth_required=auth_required)

        return inner

    def head(self, endpoint: str, auth_required: bool = False):
        """
        The @app.head decorator to add a route with HEAD method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.HEAD, endpoint, handler, auth_required=auth_required)

        return inner

    def options(self, endpoint: str, auth_required: bool = False):
        """
        The @app.options decorator to add a route with OPTIONS method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.OPTIONS, endpoint, handler, auth_required=auth_required)

        return inner

    def connect(self, endpoint: str, auth_required: bool = False):
        """
        The @app.connect decorator to add a route with CONNECT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.CONNECT, endpoint, handler, auth_required=auth_required)

        return inner

    def trace(self, endpoint: str, auth_required: bool = False):
        """
        The @app.trace decorator to add a route with TRACE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self.add_route(HttpMethod.TRACE, endpoint, handler, auth_required=auth_required)

        return inner

    def include_router(self, router):
        """
        The method to include the routes from another router

        :param router Robyn: the router object to include the routes from
        """
        self.router.routes.extend(router.router.routes)
        self.middleware_router.global_middlewares.extend(router.middleware_router.global_middlewares)
        self.middleware_router.route_middlewares.extend(router.middleware_router.route_middlewares)

        # extend the websocket routes
        prefix = router.prefix
        for route in router.web_socket_router.routes:
            new_endpoint = f"{prefix}{route}"
            self.web_socket_router.routes[new_endpoint] = router.web_socket_router.routes[route]

        self.dependencies.merge_dependencies(router)

    def configure_authentication(self, authentication_handler: AuthenticationHandler):
        """
        Configures the authentication handler for the application.

        :param authentication_handler: the instance of a class inheriting the AuthenticationHandler base class
        """
        self.authentication_handler = authentication_handler
        self.middleware_router.set_authentication_handler(authentication_handler)


class SubRouter(Robyn):
    def __init__(self, file_object: str, prefix: str = "", config: Config = Config()) -> None:
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
        app.add_response_header("Access-Control-Allow-Origin", origin)
        app.add_response_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS",
        )
        app.add_response_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        app.add_response_header("Access-Control-Allow-Credentials", "true")


__all__ = [
    "Robyn",
    "Request",
    "Response",
    "status_codes",
    "jsonify",
    "serve_file",
    "serve_html",
    "html",
    "ALLOW_CORS",
    "SubRouter",
    "AuthenticationHandler",
    "Headers",
    "WebSocketConnector",
    "WebSocket",
]
