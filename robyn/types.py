from dataclasses import dataclass
from typing import Literal, NewType, TypedDict, Union

from robyn._param_utils import QueryParamValidationError
from robyn.robyn import Url


@dataclass
class Directory:
    route: str
    directory_path: str
    show_files_listing: bool
    index_file: str | None

    def as_list(self):
        return [
            self.route,
            self.directory_path,
            self.show_files_listing,
            self.index_file,
        ]


PathParams = NewType("PathParams", dict[str, str])
Method = NewType("Method", str)
FormData = NewType("FormData", dict[str, str])
Files = NewType("Files", dict[str, bytes])
IPAddress = NewType("IPAddress", str | None)

# Convenience type aliases describing the runtime types of the components on
# ``robyn.Request``. They let editors and type checkers (mypy, pyright) validate
# handler code that reads ``request.method``, ``request.body`` and ``request.url``.
# See https://github.com/sparckles/Robyn/issues/1077.

# The HTTP methods a request can use (the value of ``request.method``).
RequestMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]

# The type of ``request.body``: text for UTF-8 payloads, raw bytes otherwise.
RequestBody = Union[str, bytes]

# The type of ``request.url`` (an alias of :class:`robyn.Url`).
RequestURL = Url


class JSONResponse(TypedDict):
    """
    A type alias for openapi response bodies. This class should be inherited by the response class type definition.
    """

    pass


class Body:
    """
    A type alias for openapi request bodies. This class should be inherited by the request body class annotation.
    """

    pass


class JsonBody:
    """
    A type alias for JSON request bodies. When used as a parameter type annotation,
    the handler receives the parsed JSON (dict) from request.json() and the OpenAPI
    docs will show a generic JSON request body input.

    Can be subclassed with annotations to provide a typed schema in the OpenAPI docs:

        class MyBody(JsonBody):
            name: str
            age: int

        @app.post("/users")
        def create_user(request: Request, data: MyBody):
            # data is the parsed JSON dict
            ...

    .. note::

        The JSON body is parsed via ``request.json()`` during parameter
        resolution, *before* the handler is invoked.  If the request body is
        not valid JSON, a 400 Bad Request response is returned automatically
        with a JSON error message (e.g., ``{"error": "Invalid JSON body: ..."}``)
        and the handler is never called.  Because parsing happens before
        handler invocation, the error **cannot** be caught with a try/except
        inside the handler.

        If you need custom error handling for malformed JSON, accept the raw
        body instead (e.g., ``body: Body``) and call ``request.json()``
        yourself inside a try/except block.
    """

    pass


__all__ = [
    "JSONResponse",
    "Body",
    "JsonBody",
    "QueryParamValidationError",
    "Directory",
    "PathParams",
    "Method",
    "FormData",
    "Files",
    "IPAddress",
    "RequestMethod",
    "RequestBody",
    "RequestURL",
]
