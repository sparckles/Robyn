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


PathParams = Dict[str, str]
RequestBody = Union[str, bytes]
RequestMethod = str
RequestURL = Url
FormData = Dict[str, str]
RequestFiles = Dict[str, bytes]
RequestIP = Optional[str]
RequestIdentity = Optional[Identity]
