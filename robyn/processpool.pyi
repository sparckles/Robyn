from numbers import Number
from robyn.robyn import SocketHeld


def spawn_process(
    directories: tuple,
    headers: tuple,
    routes: tuple,
    middlewares: tuple,
    web_sockets: list,
    event_handlers: dict,
    socket: SocketHeld,
    workers: Number,
) -> None:
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param directories tuple: the list of all the directories and related data in a tuple
    :param headers tuple: All the global headers in a tuple
    :param routes tuple: The routes touple, containing the description about every route.
    :param middlewares tuple: The middleware router touple, containing the description about every route.
    :param web_sockets list: This is a list of all the web socket routes
    :param event_handlers Dict: This is an event dict that contains the event handlers
    :param socket SocketHeld: This is the main tcp socket, which is being shared across multiple processes.
    :param process_name string: This is the name given to the process to identify the process
    :param workers number: This is the name given to the process to identify the process
    """

    pass
