from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Union

def get_version() -> str:
    pass

def jsonify(input_dict: dict) -> str:
    """
    This function serializes input dict to a json string

    Attributes:
        input_dict dict: response of the function
    """

class SocketHeld:
    def __init__(self, url: str, port: int):
        pass
    def try_clone(self) -> SocketHeld:
        pass

class MiddlewareType(Enum):
    BEFORE_REQUEST: str
    AFTER_REQUEST: str

class HttpMethod(Enum):
    GET: str
    POST: str
    PUT: str
    DELETE: str
    PATCH: str
    OPTIONS: str
    HEAD: str
    TRACE: str
    CONNECT: str

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
class Identity:
    claims: dict[str, str]

@dataclass
class QueryParams:
    """
    The query params object passed to the route handler.

    Attributes:
        queries (dict[str, list[str]]): The query parameters of the request. e.g. /user?id=123 -> {"id": "123"}
    """

    queries: dict[str, list[str]]

    def set(self, key: str, value: str) -> None:
        """
        Sets the value of the query parameter with the given key.
        If the key already exists, the value will be appended to the list of values.

        Args:
            key (str): The key of the query parameter
            value (str): The value of the query parameter
        """
        pass

    def get(self, key: str, default: Optional[str]) -> Optional[str]:
        """
        Gets the last value of the query parameter with the given key.

        Args:
            key (str): The key of the query parameter
            default (Optional[str]): The default value if the key does not exist
        """
        pass

    def empty(self) -> bool:
        """
        Returns:
            True if the query params are empty, False otherwise
        """
        pass

    def contains(self, key: str) -> bool:
        """
        Returns:
            True if the query params contain the key, False otherwise

        Args:
            key (str): The key of the query parameter
        """
        pass

    def get_first(self, key: str) -> Optional[str]:
        """
        Gets the first value of the query parameter with the given key.

        Args:
            key (str): The key of the query parameter

        """
        pass

    def get_all(self, key: str) -> Optional[list[str]]:
        """
        Gets all the values of the query parameter with the given key.

        Args:
            key (str): The key of the query parameter
        """
        pass

    def extend(self, other: QueryParams) -> None:
        """
        Extends the query params with the other query params.

        Args:
            other (QueryParams): The other QueryParams object
        """
        pass

    def to_dict(self) -> dict[str, list[str]]:
        """
        Returns:
            The query params as a dictionary
        """
        pass

    def __contains__(self, key: str) -> bool:
        pass

    def __repr__(self) -> str:
        pass

@dataclass
class Request:
    """
    The request object passed to the route handler.

    Attributes:
        query_params (QueryParams): The query parameters of the request. e.g. /user?id=123 -> {"id": "123"}
        headers (dict[str, str]): The headers of the request. e.g. {"Content-Type": "application/json"}
        params (dict[str, str]): The parameters of the request. e.g. /user/:id -> {"id": "123"}
        body (Union[str, bytes]): The body of the request. If the request is a JSON, it will be a dict.
        method (str): The method of the request. e.g. GET, POST, PUT, DELETE
        ip_addr (Optional[str]): The IP Address of the client
    """

    query_params: QueryParams
    headers: dict[str, str]
    path_params: dict[str, str]
    body: Union[str, bytes]
    method: str
    url: Url
    ip_addr: Optional[str]
    identity: Optional[Identity]

    def json(self) -> dict:
        """
        If the body is a valid JSON this will return the parsed JSON data.
        Otherwise, this will throw a ValueError.
        """
        pass

@dataclass
class Response:
    """
    The response object passed to the route handler.

    Attributes:
        status_code (int): The status code of the response. e.g. 200, 404, 500 etc.
        response_type (Optional[str]): The response type of the response. e.g. text, json, html, file etc.
        headers (dict[str, str]): The headers of the response. e.g. {"Content-Type": "application/json"}
        description (Union[str, bytes]): The body of the response. If the response is a JSON, it will be a dict.
        file_path (Optional[str]): The file path of the response. e.g. /home/user/file.txt
    """

    status_code: int
    headers: dict[str, str]
    description: Union[str, bytes]
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
        route_type: HttpMethod,
        route: str,
        function: FunctionInfo,
        is_const: bool,
    ) -> None:
        pass
    def add_global_middleware(self, middleware_type: MiddlewareType, function: FunctionInfo) -> None:
        pass
    def add_middleware_route(
        self,
        middleware_type: MiddlewareType,
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

class WebSocketConnector:
    """
    The WebSocketConnector object passed to the route handler.

    Attributes:
        id (str): The id of the client

        async_broadcast (Callable): The function to broadcast a message to all clients
        async_send_to (Callable): The function to send a message to the client
        sync_broadcast (Callable): The function to broadcast a message to all clients
        sync_send_to (Callable): The function to send a message to the client
    """

    id: str

    async def async_broadcast(self, message: str) -> None:
        pass
    async def async_send_to(self, sender_id: str, message: str) -> None:
        pass
    def sync_broadcast(self, message: str) -> None:
        pass
    def sync_send_to(self, sender_id: str, message: str) -> None:
        pass
