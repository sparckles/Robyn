from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

def get_version() -> str:
    pass

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
class Url:
    """
    The url object passed to the route handler.

    Attributes:
        scheme (str): The scheme of the url. e.g. http, https
        host (str): The host of the url. e.g. localhost,
        path (str): The path of the url. e.g. /user
    """

    scheme: str
    host: str
    path: str

@dataclass
class Request:
    """
    The request object passed to the route handler.

    Attributes:
        queries (dict[str, str]): The query parameters of the request. e.g. /user?id=123 -> {"id": "123"}
        headers (dict[str, str]): The headers of the request. e.g. {"Content-Type": "application/json"}
        params (dict[str, str]): The parameters of the request. e.g. /user/:id -> {"id": "123"}
        body (Union[str, bytes]): The body of the request. If the request is a JSON, it will be a dict.
        method (str): The method of the request. e.g. GET, POST, PUT, DELETE
    """

    queries: dict[str, str]
    headers: dict[str, str]
    path_params: dict[str, str]
    body: Union[str, bytes]
    method: str
    url: Url

@dataclass
class Response:
    """
    The response object passed to the route handler.

    Attributes:
        status_code (int): The status code of the response. e.g. 200, 404, 500 etc.
        response_type (Optional[str]): The response type of the response. e.g. text, json, html, file etc.
        headers (dict[str, str]): The headers of the response. e.g. {"Content-Type": "application/json"}
        body (Union[str, bytes]): The body of the response. If the response is a JSON, it will be a dict.
        file_path (Optional[str]): The file path of the response. e.g. /home/user/file.txt
    """

    status_code: int
    headers: dict[str, str]
    body: Union[str, bytes]
    response_type: Optional[str] = None
    file_path: Optional[str] = None

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
