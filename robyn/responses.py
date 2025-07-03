import mimetypes
import os
from typing import AsyncGenerator, Generator, Optional, Union

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


def html(html: str) -> Response:
    """
    This function will help in serving a simple html string

    :param html str: html to serve as a response
    """
    return Response(
        description=html,
        status_code=200,
        headers=Headers({"Content-Type": "text/html"}),
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


class StreamingResponse:
    def __init__(
        self,
        content: Union[Generator[str, None, None], AsyncGenerator[str, None]],
        status_code: Optional[int] = None,
        headers: Optional[Headers] = None,
        media_type: str = "text/event-stream",
    ):
        self.content = content
        self.status_code = status_code or 200
        self.headers = headers or Headers({})
        self.media_type = media_type
        
        # Set default SSE headers
        if media_type == "text/event-stream":
            self.headers.set("Content-Type", "text/event-stream")
            self.headers.set("Cache-Control", "no-cache")
            self.headers.set("Connection", "keep-alive")
            self.headers.set("Access-Control-Allow-Origin", "*")
            self.headers.set("Access-Control-Allow-Headers", "Cache-Control")


def SSE_Response(
    content: Union[Generator[str, None, None], AsyncGenerator[str, None]],
    status_code: Optional[int] = None,
    headers: Optional[Headers] = None,
) -> StreamingResponse:
    """
    Create a Server-Sent Events (SSE) streaming response.
    
    :param content: Generator or AsyncGenerator yielding SSE-formatted strings
    :param status_code: HTTP status code (default: 200)
    :param headers: Additional headers
    :return: StreamingResponse configured for SSE
    """
    return StreamingResponse(
        content=content,
        status_code=status_code,
        headers=headers,
        media_type="text/event-stream"
    )


def SSE_Message(data: str, event: Optional[str] = None, id: Optional[str] = None, retry: Optional[int] = None) -> str:
    """
    Format a message according to the SSE specification.
    
    :param data: The message data
    :param event: Optional event type
    :param id: Optional event ID
    :param retry: Optional retry time in milliseconds
    :return: SSE-formatted string
    """
    lines = []
    
    if event:
        lines.append(f"event: {event}")
    if id:
        lines.append(f"id: {id}")
    if retry:
        lines.append(f"retry: {retry}")
    
    # Handle multi-line data
    data_str = str(data) if data is not None else ""
    # Normalize line endings to \n only
    data_str = data_str.replace('\r\n', '\n').replace('\r', '\n')
    for line in data_str.split('\n'):
        lines.append(f"data: {line}")
    
    # SSE messages end with double newline
    lines.append("")
    lines.append("")
    
    return '\n'.join(lines)
