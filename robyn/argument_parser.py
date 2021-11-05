import argparse


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Robyn, a fast async web framework with a rust runtime.")
        self.parser.add_argument('--processes', type=int, default=1, required=False)
        self.parser.add_argument('--dev', default=False, type=lambda x: (str(x).lower() == 'true'))
        self.args = self.parser.parse_args()
    
    def num_processes(self):
        return self.args.processes

    def is_dev(self):
        _is_dev = self.args.dev
        if _is_dev and self.num_processes() != 1:
            raise Exception("--processes and --dev shouldn't be used together")
        return _is_dev




