import argparse


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self) -> None:
        ...

    @property
    def num_processes(self) -> int:
        ...

    @property
    def workers(self) -> int:
        ...

    @property
    def is_dev(self) -> bool:
        ...

    @property
    def log_level(self) -> str:
        ...

