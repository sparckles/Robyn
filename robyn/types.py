import typing as t
from dataclasses import dataclass
from typing import Dict, Optional, Union

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


PathParams = t.NewType("PathParams", Dict[str, str])
RequestBody = t.NewType("RequestBody", Union[str, bytes])
RequestMethod = t.NewType("RequestMethod", str)
RequestURL = t.NewType("RequestURL", Url)
FormData = t.NewType("FormData", Dict[str, str])
RequestFiles = t.NewType("RequestFiles", Dict[str, bytes])
RequestIP = t.NewType("RequestIP", Optional[str])
RequestIdentity = t.NewType("RequestIdentity", Optional[Identity])
