import asyncio
import multiprocessing as mp
import os
from inspect import signature
from typing import Callable

from multiprocess import Process
from watchdog.observers import Observer

from robyn.events import Events

from robyn.argument_parser import ArgumentParser
from robyn.dev_event_handler import EventHandler
from robyn.log_colors import Colors
from robyn.processpool import spawn_process
from robyn.responses import jsonify, static_file
from robyn.robyn import Server, SocketHeld
from robyn.router import MiddlewareRouter, Router, WebSocketRouter
from robyn.ws import WS


class Robyn:
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self, file_object: str) -> None: ...
    def before_request(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.before_request decorator to add a get route

        :param endpoint str: endpoint to server the route
        """
        ...

    def after_request(self, endpoint: str) -> Callable[..., None]:
        """
        The @app.after_request decorator to add a get route

        :param endpoint str: endpoint to server the route
        """
        ...

    def add_directory(
        self,
        route: str,
        directory_path: str,
        index_file: str = ...,
        show_files_listing: str = ...,
    ): ...
    def add_header(self, key: str, value: str) -> None: ...
    def add_web_socket(self, endpoint: str, ws: WS) -> None: ...
    def startup_handler(self, handler: Callable) -> None: ...
    def shutdown_handler(self, handler: Callable) -> None: ...
    def start(self, url: str = ..., port: int = ...) -> None:
        """
        Starts the server

        :param port int: reperesents the port number at which the server is listening
        """

        ...
    def get(self, endpoint: str, const: bool = False) -> Callable[..., None]:
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
