import argparse


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="Robyn, a fast async web framework with a rust runtime."
        )
        self.parser.add_argument(
            "--processes",
            type=int,
            default=1,
            required=False,
            help="Choose the number of processes. [Default: 1]",
        )
        self.parser.add_argument(
            "--workers",
            type=int,
            default=1,
            required=False,
            help="Choose the number of workers. [Default: 1]",
        )
        self.parser.add_argument(
            "--dev",
            dest="dev",
            action="store_true",
            default=False,
            help="Development mode. It restarts the server based on file changes.",
        )

        self.parser.add_argument(
            "--log-level",
            dest="log_level",
            default="INFO",
            help="Set the log level name",
        )

        self.args = self.parser.parse_args()

    @property
    def num_processes(self) -> int:
        return self.args.processes

    @property
    def workers(self) -> int:
        return self.args.workers

    @property
    def log_level(self) -> str:
        return self.args.log_level

    @property
    def is_dev(self) -> bool:
        _is_dev = self.args.dev
        if _is_dev and (self.num_processes != 1 or self.workers != 1):
            raise Exception("--processes and --workers shouldn't be used with --dev")
        return _is_dev
