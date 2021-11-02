# default imports
import os
import argparse
import asyncio
from inspect import signature

from .robyn import Server, SocketHeld
from .responses import static_file, jsonify
from .dev_event_handler import EventHandler
from .log_colors import Colors
from multiprocess import Process
import multiprocessing as mp
mp.allow_connection_pickling()


from watchdog.observers import Observer



def spawned_process(url, port, directories, headers, routes, socket, process_name):
    import asyncio
    import uvloop

    uvloop.install()
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    server = Server()

    print(directories)

    for directory in directories:
        route, directory_path, index_file, show_files_listing = directory
        server.add_directory(route, directory_path, index_file, show_files_listing)

    for key, val in headers:
        server.add_header(key, val)


    for route in routes:
        route_type, endpoint, handler, is_async, number_of_params = route
        server.add_route(route_type, endpoint, handler, is_async, number_of_params)

    server.start(url, port, socket, process_name)
    asyncio.get_event_loop().run_forever()




class Robyn:
    """This is the python wrapper for the Robyn binaries.
    """
    def __init__(self, file_object):
        directory_path = os.path.dirname(os.path.abspath(file_object))
        self.file_path = file_object
        self.directory_path = directory_path
        self.server = Server(directory_path)
        self.dev = self._is_dev()
        self.routes = []
        self.headers = []
        self.routes = []
        self.directories = []

    def _is_dev(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--dev', default=False, type=lambda x: (str(x).lower() == 'true'))
        return parser.parse_args().dev


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
        # read why do we need to make a tuple here
        self.routes.append(
            ( route_type, endpoint, handler, asyncio.iscoroutinefunction(handler), number_of_params)
        )

    def add_directory(self, route, directory_path, index_file=None, show_files_listing=False):
        self.directories.append(( route, directory_path, index_file, show_files_listing ))

    def add_header(self, key, value):
        self.headers.append(( key, value ))

    def remove_header(self, key):
        self.server.remove_header(key)
    
    def start(self, url="127.0.0.1", port=5000):
        """
        [Starts the server]

        :param port [int]: [reperesents the port number at which the server is listening]
        """
        socket = SocketHeld(f"0.0.0.0:{port}", port)
        if not self.dev:
            # from pathos.pools import ProcessPool
            # pool = ProcessPool(nodes=2)
            # spawned_process(url, port, self.routes, socket.try_clone(), f"Process {1}")
            # from multiprocessing import Manager, Process, Pipe
                        # p = Process(target=spawned_process, args=(url, port, self.routes, socket.try_clone(), f"Process {1}"))

            for i in range(2):
                copied = socket.try_clone()
                p = Process(
                    target=spawned_process,
                    args=(url, port, self.directories, self.headers, self.routes, copied, f"Process {i}"),
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

