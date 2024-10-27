import argparse
import os


class Config:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description="Robyn, a fast async web framework with a rust runtime.")
        self.parser = parser
        parser.add_argument(
            "--processes",
            type=int,
            default=None,
            required=False,
            help="Choose the number of processes. [Default: 1]",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=None,
            required=False,
            help="Choose the number of workers. [Default: 1]",
        )
        parser.add_argument(
            "--dev",
            dest="dev",
            action="store_true",
            default=None,
            help="Development mode. It restarts the server based on file changes.",
        )
        parser.add_argument(
            "--log-level",
            dest="log_level",
            default=None,
            help="Set the log level name",
        )
        parser.add_argument(
            "--create",
            action="store_true",
            default=False,
            help="Create a new project template.",
        )
        parser.add_argument(
            "--docs",
            action="store_true",
            default=False,
            help="Open the Robyn documentation.",
        )
        parser.add_argument(
            "--open-browser",
            action="store_true",
            default=False,
            help="Open the browser on successful start.",
        )
        parser.add_argument(
            "--version",
            action="store_true",
            default=False,
            help="Show the Robyn version.",
        )
        parser.add_argument(
            "--compile-rust-path",
            dest="compile_rust_path",
            default=None,
            help="Compile rust files in the given path.",
        )

        parser.add_argument(
            "--create-rust-file",
            dest="create_rust_file",
            default=None,
            help="Create a rust file with the given name.",
        )
        parser.add_argument(
            "--disable-openapi",
            dest="disable_openapi",
            action="store_true",
            default=False,
            help="Disable the OpenAPI documentation.",
        )
        parser.add_argument(
            "--fast",
            dest="fast",
            action="store_true",
            default=False,
            help="Fast mode. It sets the optimal values for processes, workers and log level. However, you can override them.",
        )

        args, unknown_args = parser.parse_known_args()
        self.fast = args.fast
        self.dev = args.dev
        self.processes = args.processes
        self.workers = args.workers
        self.create = args.create
        self.docs = args.docs
        self.open_browser = args.open_browser
        self.version = args.version
        self.compile_rust_path = args.compile_rust_path
        self.create_rust_file = args.create_rust_file
        self.file_path = None
        self.disable_openapi = args.disable_openapi
        self.log_level = args.log_level

        if self.fast:
            # doing this here before every other check
            # so that processes, workers and log_level can be overridden
            self.processes = self.processes or ((os.cpu_count() * 2) + 1) or 1
            self.workers = self.workers or 2
            self.log_level = self.log_level or "WARNING"

        self.processes = self.processes or 1
        self.workers = self.workers or 1

        # find something that ends with .py in unknown_args
        for arg in unknown_args:
            if arg.endswith(".py"):
                self.file_path = arg
                break

        if self.fast and self.dev:
            raise Exception("--fast and --dev shouldn't be used together")

        if self.dev and (self.processes != 1 or self.workers != 1):
            raise Exception("--processes and --workers shouldn't be used with --dev")

        if self.dev and self.log_level is None:
            self.log_level = "DEBUG"
        elif self.log_level is None:
            self.log_level = "INFO"
