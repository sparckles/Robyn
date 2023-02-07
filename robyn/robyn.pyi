from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

class SocketHeld:
    def __init__(self, url: str, port: int):
        pass
    def try_clone(self) -> SocketHeld:
        pass

@dataclass
class FunctionInfo:
    handler: Callable
    is_async: bool
    number_of_params: int

@dataclass
class Body:
    content: Union[str, bytes]

    def __add__(self, other: Union[Body, str]):
        if isinstance(other, self.__class__):
            return Body(self.content + other.content)
        elif isinstance(other, str):
            return Body(self.content + other)
        else:
            raise TypeError("unsupported operand type(s) for +: '{}' and '{}'").format(
                self.__class__, type(other)
            )

@dataclass
class Request:
    queries: dict[str, str]
    headers: dict[str, str]
    params: dict[str, str]
    body: Body

@dataclass
class Response:
    status_code: int
    headers: dict[str, str]
    body: Body

    def set_file_path(self, file_path: str):
        pass

class Server:
    def __init__(self) -> None:
        pass
    def add_directory(
        self,
        route: str,
        directory_path: str,
        show_files_listing: bool,
        index_file: Optional[str],
    ) -> None:
        pass
    def add_request_header(self, key: str, value: str) -> None:
        pass
    def add_response_header(self, key: str, value: str) -> None:
        pass
    def add_route(
        self,
        route_type: str,
        route: str,
        function: FunctionInfo,
        is_const: bool,
    ) -> None:
        pass
    def add_middleware_route(
        self,
        route_type: str,
        route: str,
        function: FunctionInfo,
    ) -> None:
        pass
    def add_startup_handler(self, function: FunctionInfo) -> None:
        pass
    def add_shutdown_handler(self, function: FunctionInfo) -> None:
        pass
    def add_web_socket_route(
        self,
        route: str,
        connect_route: FunctionInfo,
        close_route: FunctionInfo,
        message_route: FunctionInfo,
    ) -> None:
        pass
    def start(self, socket: SocketHeld, workers: int) -> None:
        pass
