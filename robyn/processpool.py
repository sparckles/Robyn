from .robyn import Server

import sys
import multiprocessing as mp
import asyncio
# import platform


mp.allow_connection_pickling()


def spawn_process(url, port, directories, headers, routes, web_sockets, socket, process_name, workers):
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param url string: the base url at which the server will listen
    :param port string: the port at which the url will listen to
    :param directories tuple: the list of all the directories and related data in a tuple
    :param headers tuple: All the global headers in a tuple
    :param routes tuple: The routes touple, containing the description about every route.
    :param socket Socket: This is the main tcp socket, which is being shared across multiple processes.
    :param process_name string: This is the name given to the process to identify the process
    :param workers number: This is the name given to the process to identify the process
    """
    # platform_name = platform.machine()   
    if sys.platform.startswith("win32") or sys.platform.startswith("linux-cross"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        # uv loop doesn't support windows or arm machines at the moment
        # but uv loop is much faster than native asyncio
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

    for endpoint in web_sockets:
        web_socket = web_sockets[endpoint]
        print(web_socket.methods)
        server.add_web_socket_route(endpoint, web_socket.methods["connect"], web_socket.methods["close"], web_socket.methods["message"])


    server.start(url, port, socket, process_name, workers)
    asyncio.get_event_loop().run_forever()
