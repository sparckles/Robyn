from typing import Dict, List

from watchdog.events import FileSystemEventHandler
from robyn.events import Events
from robyn.processpool import run_processes

from robyn.robyn import FunctionInfo
from robyn.router import MiddlewareRoute, Route
from robyn.types import Directory, Header
from robyn.ws import WS


class EventHandler(FileSystemEventHandler):
    def __init__(
        self,
        url: str,
        port: int,
        directories: List[Directory],
        request_headers: List[Header],
        routes: List[Route],
        middlewares: List[MiddlewareRoute],
        web_sockets: Dict[str, WS],
        event_handlers: Dict[Events, FunctionInfo],
        workers: int,
        processes: int,
        response_headers: List[Header],
    ) -> None:
        self.url = url
        self.port = port
        self.directories = directories
        self.request_headers = request_headers
        self.response_headers = response_headers
        self.routes = routes
        self.middlewares = middlewares
        self.web_sockets = web_sockets
        self.event_handlers = event_handlers
        self.n_workers = workers
        self.n_processes = processes
        self.processes = []

    def start_server(self):
        processes = run_processes(
            self.url,
            self.port,
            self.directories,
            self.request_headers,
            self.routes,
            self.middlewares,
            self.web_sockets,
            self.event_handlers,
            self.n_workers,
            self.n_processes,
            self.response_headers,
            True,
        )

        self.processes.extend(processes)

    def stop_server(self):
        for process in self.processes:
            process.kill()

    def on_any_event(self, event) -> None:
        """
        This function is a callback that will start a new server on every even change

        :param event FSEvent: a data structure with info about the events
        """

        for process in self.processes:
            process.kill()

        self.start_server()
