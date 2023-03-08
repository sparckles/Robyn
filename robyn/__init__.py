import asyncio
import logging
import multiprocess as mp
import os
import signal
from typing import Callable, List, Optional
from nestd import get_all_nested

from watchdog.observers import Observer

from robyn.argument_parser import Config
from robyn.dev_event_handler import EventHandler
from robyn.env_populator import load_vars
from robyn.events import Events
from robyn.logger import Colors, logger
from robyn.processpool import run_processes
from robyn.responses import jsonify, serve_file, serve_html
from robyn.robyn import FunctionInfo, Request, Response
from robyn.router import MiddlewareRouter, Router, WebSocketRouter
from robyn.types import Directory, Header
from robyn.status_codes import StatusCodes
from robyn.ws import WS


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object: str) -> None:
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.config = Config()
        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.request_headers: List[Header] = []  # This needs a better type
        self.response_headers: List[Header] = []  # This needs a better type
        self.directories: List[Directory] = []
        self.event_handlers = {}
        load_vars(project_root=directory_path)
        logging.basicConfig(level=self.config.log_level)

    def _add_route(self, route_type, endpoint, handler, is_const=False):
        """
        This is base handler for all the decorators

        :param route_type str: route type between GET/POST/PUT/DELETE/PATCH
        :param endpoint str: endpoint for the route added
        :param handler function: represents the sync or async function passed as a handler for the route
        """

        """ We will add the status code here only
        """
        return self.router.add_route(route_type, endpoint, handler, is_const)

    def before_request(self, endpoint: str) -> Callable[..., None]:
        """
        You can use the @app.before_request decorator to call a method before routing to the specified endpoint

        :param endpoint str: endpoint to server the route
        """

        return self.middleware_router.add_before_request(endpoint)

    def after_request(self, endpoint: str) -> Callable[..., None]:
        """
        You can use the @app.after_request decorator to call a method after routing to the specified endpoint

        :param endpoint str: endpoint to server the route
        """

        return self.middleware_router.add_after_request(endpoint)

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
        logger.debug(f"Add event {event_type} handler")
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

        logger.info(f"Starting server at {url}:{port}")

        mp.allow_connection_pickling()

        if not self.config.dev:
            run_processes(
                url,
                port,
                self.directories,
                self.request_headers,
                self.router.get_routes(),
                self.middleware_router.get_routes(),
                self.web_socket_router.get_routes(),
                self.event_handlers,
                self.config.workers,
                self.config.processes,
                self.response_headers,
            )
        else:
            event_handler = EventHandler(
                url,
                port,
                self.directories,
                self.request_headers,
                self.router.get_routes(),
                self.middleware_router.get_routes(),
                self.web_socket_router.get_routes(),
                self.event_handlers,
                self.config.workers,
                self.config.processes,
                self.response_headers,
            )
            event_handler.start_server()
            logger.info(
                f"Dev server initialized with the directory_path : {self.directory_path}",
                Colors.BLUE,
            )

            def terminating_signal_handler(_sig, _frame):
                logger.info("Terminating server!!", bold=True)
                event_handler.stop_server()
                observer.stop()
                observer.join()

            signal.signal(signal.SIGINT, terminating_signal_handler)
            signal.signal(signal.SIGTERM, terminating_signal_handler)

            observer = Observer()
            observer.schedule(event_handler, path=self.directory_path, recursive=True)
            observer.start()

            try:
                while observer.is_alive():
                    observer.join(1)
            finally:
                observer.stop()
                observer.join()

    def add_view(self, endpoint: str, view: Callable, const: bool = False):
        """
        This is base handler for the view decorators

        :param endpoint str: endpoint for the route added
        :param handler function: represents the function passed as a parent handler for single route with different route types
        """
        http_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

        def get_functions(view):
            functions = get_all_nested(view)
            output = []
            for name, handler in functions:
                route_type = name.upper()
                if route_type in http_methods:
                    output.append((route_type, handler))
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
            return self._add_route("GET", endpoint, handler, const)

        return inner

    def post(self, endpoint: str):
        """
        The @app.post decorator to add a route with POST method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("POST", endpoint, handler)

        return inner

    def put(self, endpoint: str):
        """
        The @app.put decorator to add a get route with PUT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("PUT", endpoint, handler)

        return inner

    def delete(self, endpoint: str):
        """
        The @app.delete decorator to add a route with DELETE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("DELETE", endpoint, handler)

        return inner

    def patch(self, endpoint: str):
        """
        The @app.patch decorator to add a route with PATCH method

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            return self._add_route("PATCH", endpoint, handler)

        return inner

    def head(self, endpoint: str):
        """
        The @app.head decorator to add a route with HEAD method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("HEAD", endpoint, handler)

        return inner

    def options(self, endpoint: str):
        """
        The @app.options decorator to add a route with OPTIONS method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("OPTIONS", endpoint, handler)

        return inner

    def connect(self, endpoint: str):
        """
        The @app.connect decorator to add a route with CONNECT method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("CONNECT", endpoint, handler)

        return inner

    def trace(self, endpoint: str):
        """
        The @app.trace decorator to add a route with TRACE method

        :param endpoint str: endpoint to server the route
        """

        def inner(handler):
            return self._add_route("TRACE", endpoint, handler)

        return inner


__all__ = [Robyn, Request, Response, StatusCodes, jsonify, serve_file, serve_html]
