# default imports
import subprocess
import os

# custom imports
from .log_colors import Colors

# third party imports
from watchdog.events import FileSystemEventHandler

def free_port(port):
    print("Running free port")
    try:
        port = int(port)
        cmd = 'lsof -t -i:{0}'.format(port)
        pid = None
        try:
            pid = subprocess.check_output(cmd, shell=True)
        except Exception:
            print("No process running on port {} by current user. Checking if root is running the proecess".format(port))
            if pid is None:
                cmd = 'sudo lsof -t -i:{0}'.format(port)
                pid = subprocess.check_output(cmd, shell=True)
        pids = pid.decode().split("\n")
        pids_int = []
        for pid in pids:
            if pid:
                pid = int(pid)
                pids_int.append(pid)
    except ValueError as e:
        print(e)
        exit()
    except Exception:
        print("No process found running on port {0}.".format(port))
        exit()

    for pid in pids_int:
        userCmd = 'ps -o user= -p {}'.format(pid)
        user = subprocess.check_output(userCmd, shell=True, text=True).rstrip('\n')

        if user.lower() == "root":
            killCmd = 'sudo kill -9 {0}'.format(pid)
        else:
            killCmd = 'kill -9 {0}'.format(pid)

        isKilled = os.system(killCmd)
        if isKilled == 0:
            print("Port {0} is free. Processs {1} killed successfully".format(port, pid))
        else:
            print("Cannot free port {0}.Failed to kill process {1}, err code:{2}".format(port, pid, isKilled))


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_name):
        self.file_name = file_name
        self.processes = []

    def start_server_first_time(self):
        if self.processes:
            raise Exception("Something wrong with the server")

        print(f"{Colors.OKGREEN}Starting the server in dev mode{Colors.ENDC}")
        self.processes.append(subprocess.Popen(["python3", self.file_name, "--reuse_port"], start_new_session=False))

    def on_any_event(self, event):
        """
        [This function is a callback that will start a new server on every even change]

        :param event [FSEvent]: [a data structure with info about the events]
        """
        if len(self.processes) > 0:
            for process in self.processes:
                free_port(5000)
                process.terminate()
        print("Bruhhh")
        self.processes.append(subprocess.Popen(["python3", self.file_name], start_new_session=False))
