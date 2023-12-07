import os
import signal
import subprocess
import sys
import time
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from robyn.logger import Colors, logger

dir_path = None

def compile_rust_files(directory_path: Optional[ str ]):
    if directory_path is None:
        global dir_path
        if dir_path is None:
            return
        directory_path = dir_path
        print("dir_path", dir_path)

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".rs"):
                file_path = os.path.join(root, file)
                file_path = os.path.abspath(file_path)
                logger.info("Compiling rust file : %s", file_path)

                result = subprocess.run(
                    ["python3", "-m", "rustimport", "build", file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=False,
                )

    return True


def setup_reloader(directory_path: str, file_path: str):
    event_handler = EventHandler(file_path)

    event_handler.reload()

    logger.info(
        "Dev server initialized with the directory_path : %s",
        directory_path,
        color=Colors.BLUE,
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
        self.process = None  # Keep track of the subprocess

        self.last_reload = time.time()  # Keep track of the last reload. EventHandler is initialized with the process.

    def stop_server(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGTERM)  # Stop the subprocess using os.kill()

    def reload(self):
        self.stop_server()

        new_env = os.environ.copy()
        new_env["IS_RELOADER_RUNNING"] = "True"  # This is used to check if a reloader is already running

        print(f"Reloading {self.file_path}...")
        arguments = [*sys.argv[1:-1]]
        compile_rust_files(None)

        self.process = subprocess.Popen(
            [sys.executable, *arguments],
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
