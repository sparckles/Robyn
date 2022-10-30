import asyncio
import sys
from typing import Dict, Tuple

from robyn.events import Events
from robyn.robyn import Server, SocketHeld
from robyn.router import MiddlewareRoute, Route
from robyn.ws import WS

Directory = Tuple[str, str, str, bool]
Header = Tuple[str, str]


def initialize_event_loop():
    # platform_name = platform.machine()
    if sys.platform.startswith("win32") or sys.platform.startswith("linux-cross"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    else:
        # uv loop doesn't support windows or arm machines at the moment
        # but uv loop is much faster than native asyncio
        import uvloop

        uvloop.install()
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def spawn_process(
    directories: Tuple[Directory, ...],
    headers: Tuple[Header, ...],
    routes: Tuple[Route, ...],
    middlewares: Tuple[MiddlewareRoute, ...],
    web_sockets: Dict[str, WS],
    event_handlers: Dict[Events, list],
    socket: SocketHeld,
    workers: int,
):
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param directories tuple: the list of all the directories and related data in a tuple
    :param headers tuple: All the global headers in a tuple
    :param routes Tuple[Route]: The routes touple, containing the description about every route.
    :param middlewares Tuple[Route]: The middleware router touple, containing the description about every route.
    :param web_sockets list: This is a list of all the web socket routes
    :param event_handlers Dict: This is an event dict that contains the event handlers
    :param socket SocketHeld: This is the main tcp socket, which is being shared across multiple processes.
    :param process_name string: This is the name given to the process to identify the process
    :param workers int: This is the name given to the process to identify the process
    """

    loop = initialize_event_loop()

    server = Server()

    # TODO: if we remove the dot access
    # the startup time will improve in the server
    for directory in directories:
        route, directory_path, index_file, show_files_listing = directory
        server.add_directory(route, directory_path, index_file, show_files_listing)

    for key, val in headers:
        server.add_header(key, val)

    for route in routes:
        route_type, endpoint, handler, is_async, number_of_params, const = route
        server.add_route(
            route_type, endpoint, handler, is_async, number_of_params, const
        )

    for route in middlewares:
        route_type, endpoint, handler, is_async, number_of_params = route
        server.add_middleware_route(
            route_type, endpoint, handler, is_async, number_of_params
        )

    if "startup" in event_handlers:
        server.add_startup_handler(
            event_handlers[Events.STARTUP][0], event_handlers[Events.STARTUP][1]
        )

    if "shutdown" in event_handlers:
        server.add_shutdown_handler(
            event_handlers[Events.SHUTDOWN][0], event_handlers[Events.SHUTDOWN][1]
        )

    for endpoint in web_sockets:
        web_socket = web_sockets[endpoint]
        server.add_web_socket_route(
            endpoint,
            web_socket.methods["connect"],
            web_socket.methods["close"],
            web_socket.methods["message"],
        )

    try:
        server.start(socket, workers)
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
