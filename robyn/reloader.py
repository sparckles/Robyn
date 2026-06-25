import glob
import os
import signal
import subprocess
import sys
import time
from typing import List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from robyn._runtime import GRACEFUL_SHUTDOWN_TIMEOUT
from robyn.logger import Colors, logger


def compile_rust_files(directory_path: str) -> list[str]:
    rust_files = glob.glob(os.path.join(directory_path, "**/*.rs"), recursive=True)
    rust_binaries: list[str] = []

    for rust_file in rust_files:
        print(f"Compiling rust file: {rust_file}")

        result = subprocess.run(
            [sys.executable, "-m", "rustimport", "build", rust_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=False,
        )
        if result.returncode != 0:
            print(f"Error compiling rust file: {rust_file} \n {result.stderr.decode('utf-8')} \n {result.stdout.decode('utf-8')}")
        else:
            print(f"Compiled rust file: {rust_file}")
            rust_file_base = rust_file.removesuffix(".rs")

            # Define the search pattern for the binary file
            if sys.platform == "win32":
                binary_extension = ".dll"
            elif sys.platform == "darwin":
                binary_extension = ".so"
            elif sys.platform == "linux":
                binary_extension = ".so"
            else:
                raise ValueError(f"Unsupported platform: {sys.platform}")

            search_pattern = f"{rust_file_base}.*{binary_extension}"
            # Use glob to find matching binary files
            matching_binaries = glob.glob(search_pattern)
            rust_binaries.extend(matching_binaries)

    return rust_binaries


def create_rust_file(file_name: str) -> None:
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
        print(
            "Error creating rust file : %s %s",
            result.stderr.decode("utf-8"),
            result.stdout.decode("utf-8"),
        )
    else:
        print("Created rust file : %s", rust_file)


def clean_rust_binaries(rust_binaries: list[str]) -> None:
    for file in rust_binaries:
        print("Cleaning rust file : %s", file)
        os.remove(file)


def setup_reloader(directory_path: str, file_path: str) -> None:
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
        event_handler.wait_for_server_shutdown()
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
        event_handler.wait_for_server_shutdown()


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, directory_path: str) -> None:
        self.file_path = file_path
        self.directory_path = directory_path
        self.process: subprocess.Popen[bytes] | None = None  # Keep track of the subprocess
        self.built_rust_binaries: List = []  # Keep track of the built rust binaries

        self.last_reload = time.time()  # Keep track of the last reload. EventHandler is initialized with the process.

    def stop_server(self) -> None:
        if self.process:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass

    def wait_for_server_shutdown(self) -> None:
        if not self.process:
            return

        try:
            self.process.wait(timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            logger.warn("Server process %s did not exit gracefully, force killing it.", self.process.pid)
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            self.process.wait()

    def reload(self) -> None:
        """Restart the app subprocess, relaunching from the resolved app file path.

        Reloading works regardless of how Robyn was started (console script,
        ``python -m robyn ...``, or as a module) because the relaunch uses the
        resolved absolute file path rather than rebuilding it from argv. See #654.
        """
        self.stop_server()
        print("Reloading the server")

        new_env = os.environ.copy()
        new_env["IS_RELOADER_RUNNING"] = "True"  # This is used to check if a reloader is already running
        # IS_RELOADER_RUNNING is specifically used for IPC between the reloader and the server

        # Forward the original CLI flags to the restarted process, but strip the
        # `--dev` flag and the single app-file token -- it is replaced below by the
        # resolved absolute path so hot reload works regardless of how Robyn was
        # started (console script, `python -m robyn ...`, or as a module). Only the
        # first matching token is dropped, so a later user arg that happens to
        # resolve to the same path is preserved. See issue #654.
        app_file = os.path.realpath(self.file_path)
        forwarded_args = []
        removed_app_token = False
        for arg in sys.argv[1:]:
            if arg == "--dev":
                continue
            if not removed_app_token and os.path.realpath(arg) == app_file:
                removed_app_token = True
                continue
            forwarded_args.append(arg)

        clean_rust_binaries(self.built_rust_binaries)
        self.built_rust_binaries = compile_rust_files(self.directory_path)

        if self.process:
            self.wait_for_server_shutdown()

        self.process = subprocess.Popen(
            [sys.executable, app_file, *forwarded_args],
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
