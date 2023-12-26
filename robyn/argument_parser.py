import argparse


class Config:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description="Robyn, a fast async web framework with a rust runtime.")
        self.parser = parser
        parser.add_argument(
            "--processes",
            type=int,
            default=1,
            required=False,
            help="Choose the number of processes. [Default: 1]",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=1,
            required=False,
            help="Choose the number of workers. [Default: 1]",
        )
        parser.add_argument(
            "--dev",
            dest="dev",
            action="store_true",
            default=False,
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

        args, unknown_args = parser.parse_known_args()

        self.processes = args.processes
        self.workers = args.workers
        self.dev = args.dev
        self.create = args.create
        self.docs = args.docs
        self.open_browser = args.open_browser
        self.version = args.version
        self.compile_rust_path = args.compile_rust_path
        self.create_rust_file = args.create_rust_file

        # find something that ends with .py in unknown_args
        for arg in unknown_args:
            if arg.endswith(".py"):
                self.file_path = arg
                break

        if self.dev and (self.processes != 1 or self.workers != 1):
            raise Exception("--processes and --workers shouldn't be used with --dev")

        if self.dev and args.log_level is None:
            self.log_level = "DEBUG"

        elif args.log_level is None:
            self.log_level = "INFO"
        else:
            self.log_level = args.log_level
