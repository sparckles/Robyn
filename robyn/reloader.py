import os
import signal
import subprocess
import sys
import time
import psutil

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from robyn.logger import Colors, logger


def setup_reloader(directory_path: str, file_path: str):
    event_handler = EventHandler(file_path)

    event_handler.reload()

    logger.info(
        f"Dev server initialized with the directory_path : {directory_path}",
        Colors.BLUE,
    )

    def terminating_signal_handler(_sig, _frame):
        event_handler.stop_server()
        logger.info("Terminating reloader", bold=True)
        observer.stop()
        observer.join()

    signal.signal(signal.SIGINT, terminating_signal_handler)
    signal.signal(signal.SIGTERM, terminating_signal_handler)

    observer = Observer()
    observer.schedule(event_handler, path=directory_path, recursive=True)
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

        self.last_reload = time.time()

    def stop_server(self):
        for process in psutil.Process().children(recursive=True):
            process.kill()
            process.wait()  # Required to avoid zombies

    def reload(self):
        self.stop_server()

        new_env = os.environ.copy()
        new_env[
            "IS_RELOADER_SETUP"
        ] = "True"  # This is used to check if a reloader is already running

        subprocess.Popen(
            [sys.executable, *sys.argv],
            env=new_env,
            start_new_session=False,
        )

        self.last_reload = time.time()

    def on_modified(self, event) -> None:
        """
        This function is a callback that will start a new server on every even change

        :param event FSEvent: a data structure with info about the events
        """

        # Avoid reloading multiple times when watchdog detects multiple events
        if time.time() - self.last_reload < 0.5:
            return

        time.sleep(0.2)  # Wait for the file to be fully written
        self.reload()
