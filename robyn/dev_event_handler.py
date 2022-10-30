import subprocess
import sys

from watchdog.events import FileSystemEventHandler


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.processes = []
        self.python_alias = (
            "python3" if not sys.platform.startswith("win32") else "python"
        )
        self.shell = True if sys.platform.startswith("win32") else False

    def start_server_first_time(self) -> None:
        if self.processes:
            raise Exception("Something wrong with the server")
        self.processes.append(
            subprocess.Popen(
                [self.python_alias, self.file_name],
                shell=self.shell,
                start_new_session=False,
            )
        )

    def on_any_event(self, event) -> None:
        """
        This function is a callback that will start a new server on every even change

        :param event FSEvent: a data structure with info about the events
        """

        if len(self.processes) > 0:
            for process in self.processes:
                process.terminate()
        self.processes.append(
            subprocess.Popen(
                [self.python_alias, self.file_name],
                shell=self.shell,
                start_new_session=False,
            )
        )
