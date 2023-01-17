from dataclasses import dataclass
from typing import Optional


@dataclass
class Directory:
    route: str
    directory_path: str
    index_file: Optional[str]
    show_files_listing: bool

    def as_list(self):
        return [
            self.route,
            self.directory_path,
            self.index_file,
            self.show_files_listing,
        ]


@dataclass
class Header:
    key: str
    val: str

    def as_list(self):
        return [self.key, self.val]
