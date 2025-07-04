import asyncio
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


class AsyncGeneratorWrapper:
    """Optimized wrapper to convert async generator to sync generator for Rust interop"""

    def __init__(self, async_gen: AsyncGenerator[str, None]):
        self.async_gen = async_gen
        self._loop = None
        self._values = []
        self._index = 0
        self._consumed = False

    def __iter__(self):
        return self

    def __next__(self):
        # If we haven't consumed the async generator yet, do it now
        if not self._consumed:
            self._consume_async_generator()

        # Return next value from pre-consumed list
        if self._index < len(self._values):
            value = self._values[self._index]
            self._index += 1
            return value
        else:
            raise StopIteration

    def _consume_async_generator(self):
        """Consume the entire async generator upfront"""
        try:
            # Get or create event loop
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            # Consume all values from async generator
            async def consume_all():
                async for value in self.async_gen:
                    self._values.append(value)

            # Run the consumption
            self._loop.run_until_complete(consume_all())
            self._consumed = True

        except Exception as e:
            # On error, mark as consumed to avoid infinite loops
            self._consumed = True
            print(f"Error consuming async generator: {e}")


class StreamingResponse:
    def __init__(
        self,
        content: Union[Generator[str, None, None], AsyncGenerator[str, None]],
        status_code: Optional[int] = None,
        headers: Optional[Headers] = None,
        media_type: str = "text/event-stream",
    ):
        # Convert async generator to sync generator if needed
        # The Rust implementation detects async generators but falls back to Python wrapper
        if hasattr(content, "__anext__"):
            # This is an async generator - wrap it with optimized wrapper
            self.content = AsyncGeneratorWrapper(content)
        else:
            # This is a sync generator - use as is
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
    return StreamingResponse(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")


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
    data_str = data_str.replace("\r\n", "\n").replace("\r", "\n")
    for line in data_str.split("\n"):
        lines.append(f"data: {line}")

    # SSE messages end with double newline
    lines.append("")
    lines.append("")

    return "\n".join(lines)
