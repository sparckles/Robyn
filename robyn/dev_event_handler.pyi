from watchdog.events import FileSystemEvent, FileSystemEventHandler

class EventHandler(FileSystemEventHandler):
    def __init__(self, file_name: str) -> None: ...
    def start_server_first_time(self) -> None: ...
    def on_any_event(self, event: FileSystemEvent) -> None:
        """
        This function is a callback that will start a new server on every even change

        :param event FSEvent: a data structure with info about the events
        """
