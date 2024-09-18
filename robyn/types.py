from dataclasses import dataclass
from typing import Dict, Optional, Union, NewType

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
RequestBody = NewType("RequestBody", Union[str, bytes])
RequestMethod = NewType("RequestMethod", str)
RequestURL = NewType("RequestURL", Url)
FormData = NewType("FormData", Dict[str, str])
RequestFiles = NewType("RequestFiles", Dict[str, bytes])
RequestIP = NewType("RequestIP", Optional[str])
RequestIdentity = NewType("RequestIdentity", Optional[Identity])
