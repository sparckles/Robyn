import asyncio
import signal
import sys
import webbrowser
from typing import Dict, List, Optional

from multiprocess import Process  # type: ignore

from robyn.events import Events
from robyn.logger import logger
from robyn.robyn import FunctionInfo, Headers, Server, SocketHeld, get_request_count
from robyn.router import GlobalMiddleware, Route, RouteMiddleware
from robyn.types import Directory


def run_processes(
    url: str,
    port: int,
    directories: List[Directory],
    request_headers: Headers,
    routes: List[Route],
    global_middlewares: List[GlobalMiddleware],
    route_middlewares: List[RouteMiddleware],
    web_sockets: Dict[str, dict],
    event_handlers: Dict[Events, FunctionInfo],
    workers: int,
    processes: int,
    response_headers: Headers,
    excluded_response_headers_paths: Optional[List[str]],
    open_browser: bool,
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
    max_requests: Optional[int] = None,
) -> List[Process]:
    import time

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
        excluded_response_headers_paths,
        client_timeout,
        keep_alive_timeout,
        max_requests,
    )

    shutting_down = False

    def terminating_signal_handler(_sig, _frame):
        nonlocal shutting_down
        shutting_down = True
        logger.info("Gracefully shutting down server...", bold=True)
        for process in process_pool:
            process.terminate()
        for process in process_pool:
            process.join(timeout=30)
            if process.is_alive():
                logger.warning("Process %s did not shut down in time, forcing kill.", process.pid)
                process.kill()
                process.join(timeout=5)
        sys.exit(0)

    signal.signal(signal.SIGINT, terminating_signal_handler)
    signal.signal(signal.SIGTERM, terminating_signal_handler)

    if open_browser:
        logger.info("Opening browser...")
        webbrowser.open_new_tab(f"http://{url}:{port}/")

    logger.info("Press Ctrl + C to stop \n")

    if max_requests and max_requests > 0 and len(process_pool) > 0:
        while not shutting_down:
            for i, process in enumerate(process_pool):
                if not process.is_alive() and not shutting_down:
                    process.join()
                    logger.info("Worker process exited (recycling), spawning replacement.")
                    copied_socket = socket.try_clone()
                    new_process = Process(
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
                            excluded_response_headers_paths,
                            client_timeout,
                            keep_alive_timeout,
                            max_requests,
                        ),
                    )
                    new_process.start()
                    process_pool[i] = new_process
            time.sleep(5)
    else:
        for process in process_pool:
            process.join()

    return process_pool


def init_processpool(
    directories: List[Directory],
    request_headers: Headers,
    routes: List[Route],
    global_middlewares: List[GlobalMiddleware],
    route_middlewares: List[RouteMiddleware],
    web_sockets: Dict[str, dict],
    event_handlers: Dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    processes: int,
    response_headers: Headers,
    excluded_response_headers_paths: Optional[List[str]],
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
    max_requests: Optional[int] = None,
) -> List[Process]:
    process_pool: List = []
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
            excluded_response_headers_paths,
            client_timeout,
            keep_alive_timeout,
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
                excluded_response_headers_paths,
                client_timeout,
                keep_alive_timeout,
                max_requests,
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
    web_sockets: Dict[str, dict],
    event_handlers: Dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    response_headers: Headers,
    excluded_response_headers_paths: Optional[List[str]],
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
    max_requests: Optional[int] = None,
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
    :param max_requests Optional[int]: Recycle this worker after N requests
    """

    loop = initialize_event_loop()

    server = Server()

    for directory in directories:
        server.add_directory(*directory.as_list())

    server.apply_request_headers(request_headers)

    server.apply_response_headers(response_headers)

    server.set_response_headers_exclude_paths(excluded_response_headers_paths)

    for route in routes:
        route_type, endpoint, function, is_const, auth_required, openapi_name, openapi_tags = route
        server.add_route(route_type, endpoint, function, is_const)

    for middleware_type, middleware_function in global_middlewares:
        server.add_global_middleware(middleware_type, middleware_function)

    for middleware_type, endpoint, function, route_type in route_middlewares:
        server.add_middleware_route(middleware_type, endpoint, function, route_type)

    if Events.STARTUP in event_handlers:
        server.add_startup_handler(event_handlers[Events.STARTUP])

    if Events.SHUTDOWN in event_handlers:
        server.add_shutdown_handler(event_handlers[Events.SHUTDOWN])

    for endpoint in web_sockets:
        web_socket = web_sockets[endpoint]
        server.add_web_socket_route(
            endpoint,
            web_socket["connect"],
            web_socket["close"],
            web_socket["message"],
        )

    try:
        server.start(socket, workers)
        loop = asyncio.get_event_loop()

        if max_requests and max_requests > 0:

            def _check_max_requests():
                if get_request_count() >= max_requests:
                    logger.info("Max requests (%d) reached, worker shutting down for recycling.", max_requests)
                    loop.stop()
                else:
                    loop.call_later(5, _check_max_requests)

            loop.call_later(5, _check_max_requests)

        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
