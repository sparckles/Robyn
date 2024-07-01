import os
import glob
import signal
import subprocess
import sys
import time
from typing import List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from robyn.logger import Colors, logger

dir_path = None


def compile_rust_files(directory_path: str):
    rust_files = glob.glob(os.path.join(directory_path, "**/*.rs"), recursive=True)
    for rust_file in rust_files:
        print("Compiling rust file : %s", rust_file)

        result = subprocess.run(
            [sys.executable, "-m", "rustimport", "build", rust_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=False,
        )
        if result.returncode != 0:
            print("Error compiling rust file : %s %s", result.stderr.decode("utf-8"), result.stdout.decode("utf-8"))
        else:
            print("Compiled rust file : %s", rust_file)

    return rust_files


def create_rust_file(file_name: str):
    if file_name.endswith(".rs"):
        file_name = file_name.removesuffix(".rs")

    rust_file = f"{file_name}.rs"

    result = subprocess.run(
        [sys.executable, "-m", "rustimport", "new", rust_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=False,
    )

    if result.returncode != 0:
        print("Error creating rust file : %s %s", result.stderr.decode("utf-8"), result.stdout.decode("utf-8"))
    else:
        print("Created rust file : %s", rust_file)


def clean_rust_binaries(rust_binaries: List[str]):
    for file in rust_binaries:
        print("Cleaning rust file : %s", file)
        os.remove(file)


def setup_reloader(directory_path: str, file_path: str):
    event_handler = EventHandler(file_path, directory_path)

    # sets the IS_RELOADER_RUNNING environment variable to True
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
    def __init__(self, file_path: str, directory_path: str) -> None:
        self.file_path = file_path
        self.directory_path = directory_path
        self.process = None  # Keep track of the subprocess
        self.built_rust_binaries = []  # Keep track of the built rust binaries

        self.last_reload = time.time()  # Keep track of the last reload. EventHandler is initialized with the process.

    def stop_server(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGTERM)  # Stop the subprocess using os.kill()

    def reload(self):
        self.stop_server()

        new_env = os.environ.copy()
        new_env["IS_RELOADER_RUNNING"] = "True"  # This is used to check if a reloader is already running

        print(f"Reloading {self.file_path}...")
        arguments = [arg for arg in sys.argv[1:] if not arg.startswith("--dev")]

        clean_rust_binaries(self.built_rust_binaries)
        self.built_rust_binaries = compile_rust_files(self.directory_path)

        prev_process = self.process
        if prev_process:
            prev_process.kill()

        self.process = subprocess.Popen(
            [sys.executable, *arguments],
            env=new_env,
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
