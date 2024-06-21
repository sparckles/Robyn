import os
from pathlib import Path
from typing import Optional

from robyn import reloader
from robyn.argument_parser import Config


def start_dev_server(config: Config, file_path: Optional[str] = None):
    """
    Start the dev server. Initialize the reloader to monitor file changes

    @param config: the config object
    @param file_path: the path to the file
    """
    if file_path is None:
        return

    absolute_file_path = (Path.cwd() / file_path).resolve()
    directory_path = absolute_file_path.parent

    if config.dev and not os.environ.get("IS_RELOADER_RUNNING", False):
        reloader.setup_reloader(config, str(directory_path), str(absolute_file_path))
        return
