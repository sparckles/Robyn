from .robyn import Server

import multiprocessing as mp
import asyncio
import uvloop


mp.allow_connection_pickling()


def spawned_process(url, port, directories, headers, routes, socket, process_name):

    uvloop.install()
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    server = Server()

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

