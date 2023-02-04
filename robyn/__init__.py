import asyncio
import logging
import multiprocessing as mp
import os
import signal
import sys
from typing import Callable, List, Optional

from multiprocess import Process  # type: ignore
from watchdog.observers import Observer

from robyn.argument_parser import ArgumentParser
from robyn.dev_event_handler import EventHandler
from robyn.env_populator import load_vars
from robyn.events import Events
from robyn.log_colors import Colors
from robyn.processpool import spawn_process
from robyn.responses import jsonify, serve_file, serve_html
from robyn.robyn import FunctionInfo, SocketHeld
from robyn.router import MiddlewareRouter, Router, WebSocketRouter
from robyn.types import Directory, Header
from robyn.ws import WS

logger = logging.getLogger(__name__)


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object: str) -> None:
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.parser = ArgumentParser()
        self.dev = self.parser.is_dev
        self.processes = self.parser.num_processes
        self.workers = self.parser.workers
        self.log_level = self.parser.log_level
        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.request_headers: List[Header] = []  # This needs a better type
        self.directories: List[Directory] = []
        self.event_handlers = {}
        load_vars(project_root=directory_path)
        self._config_logger()

    def _add_route(self, route_type, endpoint, handler, is_const=False):
        """
        [This is base handler for all the decorators]

        :param route_type [str]: [route type between GET/POST/PUT/DELETE/PATCH]
        :param endpoint [str]: [endpoint for the route added]
        :param handler [function]: [represents the sync or async function passed as a handler for the route]
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
            Directory(route, directory_path, index_file, show_files_listing)
        )

    def add_request_header(self, key: str, value: str) -> None:
        self.request_headers.append(Header(key, value))

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

        :param port int: reperesents the port number at which the server is listening
        """

        url = os.getenv("ROBYN_URL", url)
        port = int(os.getenv("ROBYN_PORT", port))

        logger.info(
            "%sStarting server at %s:%s %s", Colors.OKGREEN, url, port, Colors.ENDC
        )

        def init_processpool(socket):
            process_pool = []
            if sys.platform.startswith("win32"):
                spawn_process(
                    self.directories,
                    self.request_headers,
                    self.router.get_routes(),
                    self.middleware_router.get_routes(),
                    self.web_socket_router.get_routes(),
                    self.event_handlers,
                    socket,
                    workers,
                )

                return process_pool

            for _ in range(self.processes):
                copied_socket = socket.try_clone()
                process = Process(
                    target=spawn_process,
                    args=(
                        self.directories,
                        self.request_headers,
                        self.router.get_routes(),
                        self.middleware_router.get_routes(),
                        self.web_socket_router.get_routes(),
                        self.event_handlers,
                        copied_socket,
                        workers,
                    ),
                )
                process.start()
                process_pool.append(process)

            return process_pool

        mp.allow_connection_pickling()

        if not self.dev:
            workers = self.workers
            socket = SocketHeld(url, port)

            process_pool = init_processpool(socket)

            def terminating_signal_handler(_sig, _frame):
                logger.info(
                    f"{Colors.BOLD}{Colors.OKGREEN} Terminating server!! {Colors.ENDC}"
                )
                for process in process_pool:
                    process.kill()

            signal.signal(signal.SIGINT, terminating_signal_handler)
            signal.signal(signal.SIGTERM, terminating_signal_handler)

            logger.info(f"{Colors.OKGREEN}Press Ctrl + C to stop \n{Colors.ENDC}")
            for process in process_pool:
                process.join()
        else:
            event_handler = EventHandler(self.file_path)
            event_handler.start_server_first_time()
            logger.info(
                f"{Colors.OKBLUE}Dev server initialised with the directory_path : {self.directory_path}{Colors.ENDC}"
            )
            observer = Observer()
            observer.schedule(event_handler, path=self.directory_path, recursive=True)
            observer.start()
            try:
                while True:
                    pass
            finally:
                observer.stop()
                observer.join()

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

    def _config_logger(self):
        """
        This is the method to configure the logger either on the dev mode or the env variable
        """

        log_level = "WARN"

        if self.dev:
            log_level = "DEBUG"

        log_level = self.log_level if self.log_level else log_level
        logging.basicConfig(level=log_level)


__all__ = ["Robyn", "jsonify", "serve_file", "serve_html"]
