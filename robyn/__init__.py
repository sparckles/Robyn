from robyn.robyn import Server
from asyncio import iscoroutinefunction
from robyn.responses import static_file, jsonify

class Robyn:
    """This is the python wrapper for the Robyn binaries.
    """
    def __init__(self) -> None:
        self.server = Server()

    def add_route(self, route_type, endpoint, handler):
        """
        [This is base handler for all the decorators]

        :param route_type [str]: [route type between GET/POST/PUT/DELETE/PATCH]
        :param endpoint [str]: [endpoint for the route added]
        :param handler [function]: [represents the sync or async function passed as a handler for the route]
        """

        """ We will add the status code here only
        """
        self.server.add_route(route_type, endpoint, handler, iscoroutinefunction(handler))

    def start(self, port):
        """
        [Starts the server]

        :param port [int]: [reperesents the port number at which the server is listening]
        """
        print(f"Starting the server at port: {port}")
        self.server.start(port)

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
