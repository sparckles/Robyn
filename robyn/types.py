import typing
from dataclasses import dataclass
from typing import Optional, Dict, Union

from robyn.robyn import Url, Identity


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


PathParams = typing.NewType("PathParams", Dict[str, str])
RequestBody = typing.NewType("RequestBody", Union[str, bytes])
RequestMethod = typing.NewType("RequestMethod", str)
RequestURL = typing.NewType("RequestURL", Url)
FormData = typing.NewType("FormData", Dict[str, str])
RequestFiles = typing.NewType("RequestFiles", Dict[str, bytes])
RequestIP = typing.NewType("RequestIP", Optional[str])
RequestIdentity = typing.NewType("RequestIdentity", Optional[Identity])
