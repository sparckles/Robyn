import asyncio
import os
import signal
import sys
import time
import webbrowser

from multiprocess import Process  # type: ignore

from robyn.events import Events
from robyn.logger import logger
from robyn.robyn import FunctionInfo, Headers, Server, SocketHeld
from robyn.router import GlobalMiddleware, Route, RouteMiddleware
from robyn.types import Directory


def _raise_keyboard_interrupt(_sig, _frame):
    """SIGTERM handler that re-uses the working SIGINT/Ctrl+C shutdown path."""
    raise KeyboardInterrupt


def _graceful_shutdown_timeout() -> float:
    """Seconds to wait for workers to exit on shutdown before force-killing them.

    Configurable via the ROBYN_GRACEFUL_SHUTDOWN_TIMEOUT environment variable.
    """
    try:
        return max(0.0, float(os.getenv("ROBYN_GRACEFUL_SHUTDOWN_TIMEOUT", "10")))
    except ValueError:
        return 10.0


def run_processes(
    url: str,
    port: int,
    directories: list[Directory],
    request_headers: Headers,
    routes: list[Route],
    global_middlewares: list[GlobalMiddleware],
    route_middlewares: list[RouteMiddleware],
    web_sockets: dict[str, dict],
    event_handlers: dict[Events, FunctionInfo],
    workers: int,
    processes: int,
    response_headers: Headers,
    excluded_response_headers_paths: list[str] | None,
    open_browser: bool,
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
) -> list[Process]:
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
    )

    shutting_down = False

    def terminating_signal_handler(_sig, _frame):
        nonlocal shutting_down
        if shutting_down:
            # A second signal during shutdown -- let the default disposition hard-stop us.
            return
        shutting_down = True
        logger.info("Terminating server!!", bold=True)

        # Ask each worker to shut down gracefully (SIGTERM -> KeyboardInterrupt in the
        # worker, see spawn_process), so registered shutdown handlers run. Force-kill
        # only the workers that overrun the timeout.
        for process in process_pool:
            process.terminate()

        deadline = time.monotonic() + _graceful_shutdown_timeout()
        for process in process_pool:
            process.join(max(0.0, deadline - time.monotonic()))

        for process in process_pool:
            if process.is_alive():
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
    directories: list[Directory],
    request_headers: Headers,
    routes: list[Route],
    global_middlewares: list[GlobalMiddleware],
    route_middlewares: list[RouteMiddleware],
    web_sockets: dict[str, dict],
    event_handlers: dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    processes: int,
    response_headers: Headers,
    excluded_response_headers_paths: list[str] | None,
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
) -> list[Process]:
    process_pool: list = []
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
    directories: list[Directory],
    request_headers: Headers,
    routes: list[Route],
    global_middlewares: list[GlobalMiddleware],
    route_middlewares: list[RouteMiddleware],
    web_sockets: dict[str, dict],
    event_handlers: dict[Events, FunctionInfo],
    socket: SocketHeld,
    workers: int,
    response_headers: Headers,
    excluded_response_headers_paths: list[str] | None,
    client_timeout: int = 30,
    keep_alive_timeout: int = 20,
):
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param directories List: the list of all the directories and related data
    :param headers tuple: All the global headers in a tuple
    :param routes tuple[Route]: The routes tuple, containing the description about every route.
    :param middlewares tuple[Route]: The middleware routes tuple, containing the description about every route.
    :param web_sockets list: This is a list of all the web socket routes
    :param event_handlers Dict: This is an event dict that contains the event handlers
    :param socket SocketHeld: This is the main tcp socket, which is being shared across multiple processes.
    :param process_name string: This is the name given to the process to identify the process
    :param workers int: This is the name given to the process to identify the process
    """

    loop = initialize_event_loop()

    # Make SIGTERM behave like Ctrl+C: raise KeyboardInterrupt in the main thread so it
    # propagates out of the blocking Rust `server.start()` loop and lets registered
    # shutdown handlers run before exit. Without this, SIGTERM (multiprocessing
    # terminate(), `docker stop`, Kubernetes) is ignored by the Python side and the
    # process hangs until SIGKILL. POSIX only -- Windows has no SIGTERM delivery. See #1324.
    if not sys.platform.startswith("win32"):
        signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)

    server = Server()

    # TODO: if we remove the dot access
    # the startup time will improve in the server
    for directory in directories:
        server.add_directory(*directory.as_list())

    server.apply_request_headers(request_headers)

    server.apply_response_headers(response_headers)

    server.set_response_headers_exclude_paths(excluded_response_headers_paths)

    for route in routes:
        server.add_route(route.route_type, route.route, route.function, route.is_const)

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
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
