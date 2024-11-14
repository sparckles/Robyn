import mimetypes
import os
from typing import Optional, AsyncIterator, Iterator, Union
import asyncio

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


async def convert_sync_iterator(iterator: Iterator[str]) -> AsyncIterator[str]:
    try:
        for item in iterator:
            if item is None:
                continue
            yield str(item) if not isinstance(item, (str, bytes)) else item
    except StopIteration:
        return


class StreamingResponse:
    def __init__(
        self,
        content: Union[Iterator[str], AsyncIterator[str]],
        status_code: int = 200,
        response_type: str = "text/plain",
        description: bytes = b"",
        headers: Optional[Headers] = None
    ):
        self._content = content if asyncio.iscoroutine(content) else convert_sync_iterator(content)
        self.status_code = status_code
        self.headers = headers or Headers({})
        self.headers.set("Transfer-Encoding", "chunked")
        self.response_type = response_type
        self.description = description
        self.file_path = None
        self.is_streaming = True

    @property
    def stream(self):
        return self._content


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
