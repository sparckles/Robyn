from dataclasses import dataclass
from typing import Dict, NewType, Optional, TypedDict


@dataclass
class Directory:
    route: str
    directory_path: str
    show_files_listing: bool
    index_file: Optional[str]

    def as_list(self):
        return [
            self.route,
            self.directory_path,
            self.show_files_listing,
            self.index_file,
        ]


PathParams = NewType("PathParams", Dict[str, str])
Method = NewType("Method", str)
FormData = NewType("FormData", Dict[str, str])
Files = NewType("Files", Dict[str, bytes])
IPAddress = NewType("IPAddress", Optional[str])


class JSONResponse(TypedDict):
    """
    A type alias for openapi response bodies
    """

    pass


class Body:
    """
    A type alias for openapi request bodies
    """

    pass


class QueryParams:
    """
    A type alias for query params type annotations
    """

    pass
