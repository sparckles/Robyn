from dataclasses import dataclass
from typing import Optional


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


@dataclass
class Header:
    key: str
    val: str

    def as_list(self):
        return [self.key, self.val]
