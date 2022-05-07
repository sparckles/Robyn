import os
import asyncio
import multiprocessing as mp
from inspect import signature
from robyn.events import Events
from .robyn import Server, SocketHeld
from .argument_parser import ArgumentParser
from .responses import jsonify, static_file
from .dev_event_handler import EventHandler
from .processpool import spawn_process
from .log_colors import Colors
from .ws import WS
from .router import MiddlewareRouter, Router, WebSocketRouter
from multiprocess import Process
from watchdog.observers import Observer

from typing import Callable


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object: str) -> None:
        ...

    def before_request(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.before_request decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def after_request(self, endpoint: str):  # -> (handler: Unknown) -> None:
        """
        [The @app.after_request decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """

        ...

    def add_directory(
        self,
        route: str,
        directory_path: str,
        index_file: str = ...,
        show_files_listing: str = ...,
    ):
        ...

    def add_header(self, key: str, value: str) -> None:
        ...

    def add_web_socket(self, endpoint: str, ws: WS) -> None:
        ...

    def startup_handler(self, handler: Callable) -> None:
        ...

    def shutdown_handler(self, handler: Callable) -> None:
        ...

    def start(self, url: str = ..., port: int = ...) -> None:
        """
        Starts the server

        :param port int: reperesents the port number at which the server is listening
        """

        ...

    def get(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.get decorator to add a get route

        :param endpoint str: endpoint to server the route
        """
        ...

    def post(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.post decorator to add a get route

        :param endpoint str: endpoint to server the route
        """
        ...

    def put(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.put decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def delete(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.delete decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def patch(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.patch decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def head(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.head decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def options(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.options decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...

    def connect(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.connect decorator to add a get route

        :param endpoint str: endpoint to server the route
        """
        ...

    def trace(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.trace decorator to add a get route

        :param endpoint str: endpoint to server the route
        """

        ...
