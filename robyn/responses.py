import mimetypes
import os
from typing import Optional, Any, Union, Callable, Iterator, AsyncIterator, Dict

from robyn.robyn import Headers, Response


class FileResponse:
    def __init__(
        self,
        file_path: str,
        status_code: Optional[int] = None,
        headers: Optional[Headers] = None,
    ):
        self.file_path = file_path
        self.description = ""
        self.status_code = status_code or 200
        self.headers = headers or Headers({"Content-Disposition": "attachment"})


def html(html: str, streaming: bool = False) -> Response:
    """
    This function will help in serving a simple html string or stream

    :param html str: html to serve as a response
    :param streaming bool: whether to treat the response as a streaming response
    """
    return Response(
        description=html,
        status_code=200,
        headers=Headers({"Content-Type": "text/html"}),
        streaming=streaming,
    )


def serve_html(file_path: str) -> FileResponse:
    """
    This function will help in serving a single html file

    :param file_path str: file path to serve as a response
    """

    return FileResponse(file_path, headers=Headers({"Content-Type": "text/html"}))


def serve_file(file_path: str, file_name: Optional[str] = None) -> FileResponse:
    """
    This function will help in serving a file

    :param file_path str: file path to serve as a response
    :param file_name [str | None]: file name to serve as a response, defaults to None
    """
    file_name = file_name or os.path.basename(file_path)

    mime_type = mimetypes.guess_type(file_name)[0]

    headers = Headers({"Content-Type": mime_type})
    headers.append("Content-Disposition", f"attachment; filename={file_name}")

    return FileResponse(
        file_path,
        headers=headers,
    )


class Response:
    def __init__(
        self,
        status_code: int,
        headers: Union[Headers, Dict[str, str]],
        description: Union[str, bytes, Iterator[Union[str, bytes]], AsyncIterator[Union[str, bytes]]],
        streaming: bool = False,
    ) -> None:
        """
        Create a new Response object.
        """
        self.status_code = status_code
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.file_path = None
        self.streaming = streaming

        # For error responses, ensure proper headers
        if status_code >= 400:
            self.headers.set("Content-Type", "text/plain")
            self.headers.set("X-Error-Response", "true")
            self.headers.set("global_after", "global_after_request")
            self.headers.set("server", "robyn")

        # Convert description to bytes if it's a string
        if isinstance(description, str):
            self.description = description.encode()
        elif isinstance(description, bytes):
            self.description = description
        elif isinstance(description, (Iterator, AsyncIterator)):
            self.description = description
        else:
            # Convert any other type to string and then bytes
            self.description = str(description).encode()

    def __str__(self) -> str:
        """
        Return a string representation of the Response object.
        """
        return f"Response(status_code={self.status_code}, headers={self.headers}, description={self.description})"
