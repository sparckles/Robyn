import asyncio
import mimetypes
import os
import threading
from typing import AsyncGenerator, Generator, Optional, Union

from robyn.robyn import Headers, Response


class FileResponse:
    def __init__(
        self,
        file_path: str,
        status_code: int | None = None,
        headers: Headers | None = None,
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


def serve_file(file_path: str, file_name: str | None = None) -> FileResponse:
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
    """Drive an async generator through Robyn's synchronous streaming protocol.

    The generator is driven on the event loop that was running when the
    ``StreamingResponse`` was constructed — i.e. the handler's loop. That keeps
    any async resources created in the handler (DB sessions, HTTP clients) on
    the loop they are bound to, so ``await``-ing them inside the generator works
    instead of raising "attached to a different loop" (#1219). When constructed
    outside an async context (a sync handler), a dedicated background loop is
    used instead.

    Errors raised by the generator are propagated (not swallowed), so a failing
    stream surfaces the real traceback in the server logs rather than silently
    truncating.
    """

    def __init__(self, async_gen: AsyncGenerator[Union[str, bytes], None]):
        self._async_gen = async_gen
        self._iterator: Optional[AsyncGenerator] = None
        self._exhausted = False
        self._owns_loop = False
        self._thread: Optional[threading.Thread] = None
        try:
            # Constructed inside an async handler -> reuse its running loop.
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # Constructed in a sync handler -> drive on a dedicated background loop.
            self._loop = asyncio.new_event_loop()
            self._owns_loop = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def __iter__(self):
        return self

    def __next__(self):
        if self._exhausted:
            raise StopIteration

        if self._iterator is None:
            self._iterator = self._async_gen.__aiter__()

        # Schedule one step on the owning loop and block until it yields a value.
        # run_coroutine_threadsafe is safe to call from the worker thread Robyn
        # drives the stream on, and works whether or not we own the loop.
        future = asyncio.run_coroutine_threadsafe(self._iterator.__anext__(), self._loop)
        try:
            return future.result()
        except StopAsyncIteration:
            self._finish()
            raise StopIteration
        except BaseException:
            # Surface real errors instead of silently ending the stream.
            self._finish()
            raise

    def _finish(self):
        self._exhausted = True
        if self._owns_loop:
            self._loop.call_soon_threadsafe(self._loop.stop)


class StreamingResponse:
    def __init__(
        self,
        content: Generator[str | bytes, None, None] | AsyncGenerator[str | bytes, None],
        status_code: int | None = None,
        headers: Headers | None = None,
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


def SSEResponse(
    content: Generator[str | bytes, None, None] | AsyncGenerator[str | bytes, None],
    status_code: int | None = None,
    headers: Headers | None = None,
) -> StreamingResponse:
    """
    Create a Server-Sent Events (SSE) streaming response.

    :param content: Generator or AsyncGenerator yielding SSE-formatted strings
    :param status_code: HTTP status code (default: 200)
    :param headers: Additional headers
    :return: StreamingResponse configured for SSE
    """
    return StreamingResponse(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")


def SSEMessage(data: str, event: str | None = None, id: str | None = None, retry: int | None = None) -> str:
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
