from .robyn import Server
from asyncio import iscoroutinefunction
from .responses import static_file

class Robyn:
    """This is the python wrapper for the Robyn binaries.
    """
    def __init__(self) -> None:
        self.server = Server()

    def add_route(self, route_type, endpoint, handler):
        """ We will add the status code here only
        """
        self.server.add_route(route_type, endpoint, handler, iscoroutinefunction(handler))

    def start(self, port):
        print(f"Starting the server at port: {port}")
        self.server.start(port)

    def get(self, endpoint):
        def inner(handler):
            self.add_route("GET", endpoint, handler)
        return inner
    
    def post(self, endpoint):
        def inner(handler):
            self.add_route("POST", endpoint, handler)
        return inner

    def put(self, endpoint):
        def inner(handler):
            self.add_route("PUT", endpoint, handler)
        return inner

    def delete(self, endpoint):
        def inner(handler):
            self.add_route("DELETE", endpoint, handler)
        return inner

    def patch(self, endpoint):
        def inner(handler):
            self.add_route("PATCH", endpoint, handler)
        return inner
