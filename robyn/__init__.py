# default imports
import os
import asyncio
from inspect import signature
import multiprocessing as mp
mp.allow_connection_pickling()

# custom imports and exports
from .robyn import Server, SocketHeld
from .argument_parser import ArgumentParser
from .responses import static_file, jsonify
from .dev_event_handler import EventHandler
from .processpool import spawn_process
from .log_colors import Colors
from .ws import WS


# 3rd party imports and exports
from multiprocess import Process
from watchdog.observers import Observer



class Robyn:
    """This is the python wrapper for the Robyn binaries.
    """
    def __init__(self, file_object):
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.server = Server(directory_path)
        self.parser = ArgumentParser()
        self.dev = self.parser.is_dev()
        self.processes = self.parser.num_processes() 
        self.workers = self.parser.workers()
        self.routes = []
        self.headers = []
        self.routes = []
        self.directories = []
        self.web_sockets = {}


    def add_route(self, route_type, endpoint, handler):
        """
        [This is base handler for all the decorators]

        :param route_type [str]: [route type between GET/POST/PUT/DELETE/PATCH]
        :param endpoint [str]: [endpoint for the route added]
        :param handler [function]: [represents the sync or async function passed as a handler for the route]
        """

        """ We will add the status code here only
        """
        number_of_params = len(signature(handler).parameters)
        self.routes.append(
            ( route_type, endpoint, handler, asyncio.iscoroutinefunction(handler), number_of_params)
        )

    def add_directory(self, route, directory_path, index_file=None, show_files_listing=False):
        self.directories.append(( route, directory_path, index_file, show_files_listing ))

    def add_header(self, key, value):
        self.headers.append(( key, value ))

    def remove_header(self, key):
        self.server.remove_header(key)

    def add_web_socket(self, endpoint, ws):
        self.web_sockets[endpoint] = ws
        
    
    def start(self, url="127.0.0.1", port=5000):
        """
        [Starts the server]

        :param port [int]: [reperesents the port number at which the server is listening]
        """
        socket = SocketHeld(url, port)
        workers = self.workers
        if not self.dev:
            for process_number in range(self.processes):
                copied = socket.try_clone()
                p = Process(
                    target=spawn_process,
                    args=(url, port, self.directories, self.headers, self.routes, self.web_sockets, copied, f"Process {process_number}", workers),
                )
                p.start()

            input("Press Cntrl + C to stop \n")
        else:
            event_handler = EventHandler(self.file_path)
            event_handler.start_server_first_time()
            print(f"{Colors.OKBLUE}Dev server initialised with the directory_path : {self.directory_path}{Colors.ENDC}")
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

    def head(self, endpoint):
        """
        [The @app.head decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("HEAD", endpoint, handler)

        return inner

    def options(self, endpoint):
        """
        [The @app.options decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("OPTIONS", endpoint, handler)

        return inner


    def connect(self, endpoint):
        """
        [The @app.connect decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("CONNECT", endpoint, handler)

        return inner

    def trace(self, endpoint):
        """
        [The @app.trace decorator to add a get route]

        :param endpoint [str]: [endpoint to server the route]
        """
        def inner(handler):
            self.add_route("TRACE", endpoint, handler)

        return inner


