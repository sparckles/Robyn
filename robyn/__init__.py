<<<<<<< HEAD
from robyn.robyn import Server
=======
# default imports
import os
import subprocess

import argparse
from .robyn import Server
>>>>>>> 836c79c (Implement a working dev server)
from asyncio import iscoroutinefunction
from robyn.responses import static_file, jsonify
from inspect import signature

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def __init__(self, file_name):
        self.file_name = file_name
        self.processes = []

    def on_any_event(self, event):
        if len(self.processes)>0:
            for process in self.processes:
                process.terminate()
        self.processes.append(subprocess.Popen(["python3",self.file_name], start_new_session=False))

class Robyn:
<<<<<<< HEAD
    """This is the python wrapper for the Robyn binaries."""

    def __init__(self) -> None:
        self.server = Server()
=======
    """This is the python wrapper for the Robyn binaries.
    """
    def __init__(self, file_object):
        directory_path = os.path.dirname(os.path.dirname(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.server = Server(directory_path)
        self.dev = self._is_dev()
        print(f"Self is dev {self.dev}")

    def _is_dev(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--dev', default=False, type=lambda x: (str(x).lower() == 'true'))
        return parser.parse_args().dev

>>>>>>> 836c79c (Implement a working dev server)

    def add_route(self, route_type, endpoint, handler):
        """
        [This is base handler for all the decorators]

        :param route_type [str]: [route type between GET/POST/PUT/DELETE/PATCH]
        :param endpoint [str]: [endpoint for the route added]
        :param handler [function]: [represents the sync or async function passed as a handler for the route]
        """

        """ We will add the status code here only
        """
        self.server.add_route(
            route_type, endpoint, handler, iscoroutinefunction(handler)
        )

    def add_header(self, key, value):
        self.server.add_header(key, value)

    def remove_header(self, key):
        self.server.remove_header(key)


    
    def start(self, port):
        """
        [Starts the server]

        :param port [int]: [reperesents the port number at which the server is listening]
        """
        print(f"Starting the server at port: {port}")
        self.server.start_dev_server(port)
        if not self.dev:
            self.server.start(port)
        else:
            event_handler = MyHandler(self.file_path)
            observer = Observer()
            observer.schedule(event_handler, path=self.directory_path, recursive=True)
            observer.start()
            try:
                while True:
                    pass
            finally:
                observer.stop()
                observer.join()

    def get(self, endpoint):
        """
        [The @app.get decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("GET", endpoint, handler)

        return inner

    def post(self, endpoint):
        """
        [The @app.post decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            sig = signature(handler)
            params = len(sig.parameters)
            if params != 1:
                print("We need one argument on post.")
                return
            self.add_route("POST", endpoint, handler)

        return inner

    def put(self, endpoint):
        """
        [The @app.put decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("PUT", endpoint, handler)

        return inner

    def delete(self, endpoint):
        """
        [The @app.delete decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("DELETE", endpoint, handler)

        return inner

    def patch(self, endpoint):
        """
        [The @app.patch decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("PATCH", endpoint, handler)
            
        return inner
