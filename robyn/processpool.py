import asyncio
import webbrowser
from multiprocess import Process
import signal
import sys
from typing import Dict, List
from robyn.logger import logger

from robyn.events import Events
from robyn.robyn import FunctionInfo, Headers, Server, SocketHeld
from robyn.router import GlobalMiddleware, RouteMiddleware, Route
from robyn.types import Directory
from robyn.ws import WebSocket


def run_processes(
    url: str,
    port: int,
    directories: List[Directory],
    request_headers: Headers,
    routes: List[Route],
    global_middlewares: List[GlobalMiddleware],
    route_middlewares: List[RouteMiddleware],
    web_sockets: Dict[str, WebSocket],
    event_handlers: Dict[Events, FunctionInfo],
    workers: int,
    processes: int,
    response_headers: Headers,
    open_browser: bool,
) -> List[Process]:
    socket = SocketHeld(url, port)

    process_pool = init_processpool(
        directories,
        request_headers,
        routes,
        global_middlewares,
        route_middlewares,
        web_sockets,
        event_handlers,
        socket,
        workers,
        processes,
        response_headers,
    )

    def terminating_signal_handler(_sig, _frame):
        logger.info("Terminating server!!", bold=True)
        for process in process_pool:
            process.kill()

    signal.signal(signal.SIGINT, terminating_signal_handler)
    signal.signal(signal.SIGTERM, terminating_signal_handler)

    if open_browser:
        logger.info("Opening browser...")
        webbrowser.open_new_tab(f"http://{url}:{port}/")

    logger.info("Press Ctrl + C to stop \n")
    for process in process_pool:
        process.join()

    return process_pool


def init_processpool(
    directories: List[Directory],
    request_headers: Headers,
    routes: List[Route],
    global_middlewares: List[GlobalMiddleware],
    route_middlewares: List[RouteMiddleware],
    web_sockets: Dict[str, WebSocket],
    event_handlers: Dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    processes: int,
    response_headers: Headers,
) -> List[Process]:
    process_pool = []
    if sys.platform.startswith("win32") or processes == 1:
        spawn_process(
            directories,
            request_headers,
            routes,
            global_middlewares,
            route_middlewares,
            web_sockets,
            event_handlers,
            socket,
            workers,
            response_headers,
        )

        return process_pool

    for _ in range(processes):
        copied_socket = socket.try_clone()
        process = Process(
            target=spawn_process,
            args=(
                directories,
                request_headers,
                routes,
                global_middlewares,
                route_middlewares,
                web_sockets,
                event_handlers,
                copied_socket,
                workers,
                response_headers,
            ),
        )
        process.start()
        process_pool.append(process)

    return process_pool


def initialize_event_loop():
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
    directories: List[Directory],
    request_headers: Headers,
    routes: List[Route],
    global_middlewares: List[GlobalMiddleware],
    route_middlewares: List[RouteMiddleware],
    web_sockets: Dict[str, WebSocket],
    event_handlers: Dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    response_headers: Headers,
):
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param directories List: the list of all the directories and related data
    :param headers tuple: All the global headers in a tuple
    :param routes Tuple[Route]: The routes tuple, containing the description about every route.
    :param middlewares Tuple[Route]: The middleware routes tuple, containing the description about every route.
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
        server.add_directory(*directory.as_list())

    server.apply_request_headers(request_headers)

    server.apply_response_headers(response_headers)

    for route in routes:
        route_type, endpoint, function, is_const = route
        server.add_route(route_type, endpoint, function, is_const)

    for middleware_type, middleware_function in global_middlewares:
        server.add_global_middleware(middleware_type, middleware_function)

    for route_type, endpoint, function in route_middlewares:
        server.add_middleware_route(route_type, endpoint, function)

    if Events.STARTUP in event_handlers:
        server.add_startup_handler(event_handlers[Events.STARTUP])

    if Events.SHUTDOWN in event_handlers:
        server.add_shutdown_handler(event_handlers[Events.SHUTDOWN])

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
