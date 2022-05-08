from __future__ import annotations

from typing import Callable, Optional, Tuple

class SocketHeld:
    def __init__(self, url: str, port: int):
        pass
    def try_clone(self) -> SocketHeld:
        pass

class Server:
    def __init__(self):
        pass
    def add_directory(
        self,
        route: str,
        directory_path: str,
        index_file: Optional[str],
        show_files_listing: bool,
    ):
        pass
    def add_header(self, key: str, value: str):
        pass
    def add_route(
        self,
        route_type: str,
        route: str,
        handler: Callable,
        is_async: bool,
        number_of_params: int,
    ):
        pass
    def add_middleware_route(
        self,
        route_type: str,
        route: str,
        handler: Callable,
        is_async: bool,
        number_of_params: int,
    ):
        pass
    def add_startup_handler(self, handler: Callable, is_async: bool):
        pass
    def add_shutdown_handler(self, handler: Callable, is_async: bool):
        pass
    def add_web_socket_route(
        self,
        route: str,
        connect_route: Tuple[Callable, bool, int],
        close_route: Tuple[Callable, bool, int],
        message_route: Tuple[Callable, bool, int],
    ):
        pass
    def start(self, socket: SocketHeld, workers: int):
        pass
