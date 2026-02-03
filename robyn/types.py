from dataclasses import dataclass
from typing import NewType, TypeAlias, TypedDict


@dataclass
class Directory:
    route: str
    directory_path: str
    show_files_listing: bool
    index_file: str | None = None

    def as_list(self):
        return [
            self.route,
            self.directory_path,
            self.show_files_listing,
            self.index_file,
        ]


PathParams: TypeAlias = dict[str, str]
Method = NewType("Method", str)
FormData: TypeAlias = dict[str, str]
Files: TypeAlias = dict[str, bytes]
IPAddress: TypeAlias = str | None


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


__all__ = ["JSONResponse", "Body"]
