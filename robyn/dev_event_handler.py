# default imports
import subprocess

# custom imports
from .log_colors import Colors

# third party imports
from watchdog.events import FileSystemEventHandler



class EventHandler(FileSystemEventHandler):
    def __init__(self, file_name):
        self.file_name = file_name
        self.processes = []

    def start_server_first_time(self):
        if self.processes:
            raise Exception("Something wrong with the server")

        print(f"{Colors.OKGREEN}Starting the server in dev mode{Colors.ENDC}")
        self.processes.append(subprocess.Popen(["python3", self.file_name], start_new_session=False))

    def on_any_event(self, event):
        """
        [This function is a callback that will start a new server on every even change]

        :param event [FSEvent]: [a data structure with info about the events]
        """
        if len(self.processes)>0:
            for process in self.processes:
                process.terminate()
        print(f"{Colors.OKGREEN}Starting the server in dev mode{Colors.ENDC}")
        self.processes.append(subprocess.Popen(["python3", self.file_name], start_new_session=False))
