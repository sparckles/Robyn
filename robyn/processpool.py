from .robyn import Server

import multiprocessing as mp
import asyncio
import uvloop


mp.allow_connection_pickling()


def spawn_process(url, port, directories, headers, routes, socket, process_name):
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
    """
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
