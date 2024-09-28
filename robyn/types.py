from dataclasses import dataclass
from typing import Dict, Optional, NewType, TypedDict

from robyn.robyn import Identity, Url


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
RequestMethod = NewType("RequestMethod", str)
RequestURL = NewType("RequestURL", Url)
FormData = NewType("FormData", Dict[str, str])
RequestFiles = NewType("RequestFiles", Dict[str, bytes])
RequestIP = NewType("RequestIP", Optional[str])
RequestIdentity = NewType("RequestIdentity", Optional[Identity])


class JSONResponse(TypedDict):
    """
    A base class to override to implement openapi response bodies
    """

    pass


class RequestBody:
    """
    A base class to override to implement openapi request bodies
    """

    pass


class QueryParams:
    """
    A base class to override to implement query params type annotations in openapi
    """

    pass
