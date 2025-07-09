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
    """Optimized true-streaming wrapper for async generators"""

    def __init__(self, async_gen: AsyncGenerator[str, None]):
        self.async_gen = async_gen
        self._loop = None
        self._iterator = None
        self._exhausted = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._exhausted:
            raise StopIteration

        # Initialize the loop and iterator only once
        if self._iterator is None:
            self._init_async_iterator()

        try:
            # Get the next value from the async generator
            # This is the key optimization - we don't buffer, we get one value at a time
            return self._get_next_value()
        except StopIteration:
            self._exhausted = True
            raise

    def _init_async_iterator(self):
        """Initialize the async iterator with proper loop handling"""
        try:
            # Try to get the running event loop
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # Create the async iterator
        self._iterator = self.async_gen.__aiter__()

    def _get_next_value(self):
        """Get the next value from async generator without buffering"""
        try:
            # Create a coroutine to get the next value
            async def get_next():
                return await self._iterator.__anext__()

            # Run the coroutine to get the next value
            return self._loop.run_until_complete(get_next())
        except StopAsyncIteration:
            # Convert StopAsyncIteration to StopIteration for sync generator protocol
            raise StopIteration
        except Exception as e:
            # Log error and stop iteration
            print(f"Error in async generator: {e}")
            raise StopIteration


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
            # Cache-Control and Connection headers are set by Rust layer with optimized headers
            self.headers.set("Access-Control-Allow-Origin", "*")
            self.headers.set("Access-Control-Allow-Headers", "Cache-Control")


def SSEResponse(
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


def SSEMessage(data: str, event: Optional[str] = None, id: Optional[str] = None, retry: Optional[int] = None) -> str:
    """
    Optimized SSE message formatting with minimal allocations.

    :param data: The message data
    :param event: Optional event type
    :param id: Optional event ID
    :param retry: Optional retry time in milliseconds
    :return: SSE-formatted string
    """
    # Pre-calculate size to avoid multiple string concatenations
    parts = []

    # Add optional fields first
    if event:
        parts.append(f"event: {event}\n")
    if id:
        parts.append(f"id: {id}\n")
    if retry:
        parts.append(f"retry: {retry}\n")

    # Handle data with optimized multi-line processing
    if data:
        data_str = str(data)
        # Fast path for single-line data (most common case)
        if "\n" not in data_str and "\r" not in data_str:
            parts.append(f"data: {data_str}\n")
        else:
            # Multi-line data handling
            normalized_data = data_str.replace("\r\n", "\n").replace("\r", "\n")
            for line in normalized_data.split("\n"):
                parts.append(f"data: {line}\n")
    else:
        parts.append("data: \n")

    # Add the required double newline terminator
    parts.append("\n")

    # Single join operation for optimal performance
    return "".join(parts)
