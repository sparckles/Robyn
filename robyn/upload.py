import io
import mimetypes
from typing import Optional


class UploadFile:
    """Represents an uploaded file from a multipart form request.

    Provides convenient access to file metadata and content. Wraps the raw
    bytes from ``request.files`` with filename, content type, and file-like
    read access.

    Usage::

        @app.post("/upload")
        async def upload(request: Request):
            raw_files = request.files
            for name, data in raw_files.items():
                file = UploadFile(filename=name, file=data)
                contents = file.read()
                print(f"Got {file.filename} ({file.content_type}): {file.size} bytes")
    """

    __slots__ = ("filename", "content_type", "file", "_size")

    def __init__(
        self,
        file: bytes,
        *,
        filename: str = "upload",
        content_type: Optional[str] = None,
    ) -> None:
        self.filename = filename
        self.content_type = content_type or self._guess_content_type(filename)
        self.file = io.BytesIO(file) if isinstance(file, (bytes, bytearray)) else file
        self._size: Optional[int] = len(file) if isinstance(file, (bytes, bytearray)) else None

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    @property
    def size(self) -> int:
        if self._size is None:
            pos = self.file.tell()
            self.file.seek(0, 2)
            self._size = self.file.tell()
            self.file.seek(pos)
        return self._size

    def read(self, size: int = -1) -> bytes:
        return self.file.read(size)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self.file.seek(offset, whence)

    def tell(self) -> int:
        return self.file.tell()

    def close(self) -> None:
        self.file.close()

    def __repr__(self) -> str:
        return f"UploadFile(filename={self.filename!r}, content_type={self.content_type!r}, size={self.size})"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
