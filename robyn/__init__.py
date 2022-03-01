# default imports
import os
import asyncio
from inspect import signature
import multiprocessing as mp
from robyn.events import Events

# custom imports and exports
from .robyn import Server, SocketHeld
from .argument_parser import ArgumentParser
from .responses import static_file, jsonify
from .dev_event_handler import EventHandler
from .processpool import spawn_process
from .log_colors import Colors
from .ws import WS
from .router import Router, MiddlewareRouter, WebSocketRouter

# 3rd party imports and exports
from multiprocess import Process
from watchdog.observers import Observer

mp.allow_connection_pickling()


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object):
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.parser = ArgumentParser()
        self.dev = self.parser.is_dev()
        self.processes = self.parser.num_processes()
        self.workers = self.parser.workers()
        self.router = Router()
        self.middleware_router = MiddlewareRouter()
        self.web_socket_router = WebSocketRouter()
        self.headers = []
        self.directories = []
        self.event_handlers = {}

    def _add_route(self, route_type, endpoint, handler):
        """
        [This is base handler for all the decorators]

        :param route_type [str]: [route type between GET/POST/PUT/DELETE/PATCH]
        :param endpoint [str]: [endpoint for the route added]
        :param handler [function]: [represents the sync or async function passed as a handler for the route]
        """

        """ We will add the status code here only
        """
        self.router.add_route(route_type, endpoint, handler)

    def before_request(self, endpoint):
        """
        [The @app.before_request decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        return self.middleware_router.add_before_request(endpoint)

    def after_request(self, endpoint):
        """
        [The @app.after_request decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        return self.middleware_router.add_after_request(endpoint)

    def add_directory(
        self, route, directory_path, index_file=None, show_files_listing=False
    ):
        self.directories.append((route, directory_path, index_file, show_files_listing))

    def add_header(self, key, value):
        self.headers.append((key, value))

    def add_web_socket(self, endpoint, ws):
        self.web_socket_router.add_route(endpoint, ws)

    def _add_event_handler(self, event_type: str, handler):
        print(f"Add event {event_type} handler")
        if event_type not in {Events.STARTUP, Events.SHUTDOWN}:
            return

        is_async = asyncio.iscoroutinefunction(handler)
        self.event_handlers[event_type] = (handler, is_async)

    def startup_handler(self, handler):
        self._add_event_handler(Events.STARTUP, handler)

    def shutdown_handler(self, handler):
        self._add_event_handler(Events.SHUTDOWN, handler)

    def start(self, url="127.0.0.1", port=5000):
        """
        [Starts the server]

        :param port [int]: [reperesents the port number at which the server is listening]
        """
        if not self.dev:
            workers = self.workers
            socket = SocketHeld(url, port)
            for _ in range(self.processes):
                copied_socket = socket.try_clone()
                p = Process(
                    target=spawn_process,
                    args=(
                        self.directories,
                        self.headers,
                        self.router.get_routes(),
                        self.middleware_router.get_routes(),
                        self.web_socket_router.get_routes(),
                        self.event_handlers,
                        copied_socket,
                        workers,
                    ),
                )
                p.start()

            print("Press Ctrl + C to stop \n")
        else:
            event_handler = EventHandler(self.file_path)
            event_handler.start_server_first_time()
            print(
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

    def get(self, endpoint):
        """
        [The @app.get decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("GET", endpoint, handler)

        return inner

    def post(self, endpoint):
        """
        [The @app.post decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("POST", endpoint, handler)

        return inner

    def put(self, endpoint):
        """
        [The @app.put decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("PUT", endpoint, handler)

        return inner

    def delete(self, endpoint):
        """
        [The @app.delete decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("DELETE", endpoint, handler)

        return inner

    def patch(self, endpoint):
        """
        [The @app.patch decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("PATCH", endpoint, handler)

        return inner

    def head(self, endpoint):
        """
        [The @app.head decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("HEAD", endpoint, handler)

        return inner

    def options(self, endpoint):
        """
        [The @app.options decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("OPTIONS", endpoint, handler)

        return inner

    def connect(self, endpoint):
        """
        [The @app.connect decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("CONNECT", endpoint, handler)

        return inner

    def trace(self, endpoint):
        """
        [The @app.trace decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        def inner(handler):
            self._add_route("TRACE", endpoint, handler)

        return inner
