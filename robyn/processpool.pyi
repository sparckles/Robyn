from numbers import Number
from typing import Dict, Tuple

from robyn.events import Events
from robyn.robyn import SocketHeld
from robyn.router import Route
from robyn.ws import WS

Directory = Tuple[str, str, str, str]
Header = Tuple[str, str]

def spawn_process(
    directories: Tuple[Directory, ...],
    headers: Tuple[Header, ...],
    routes: Tuple[Route, ...],
    middlewares: Tuple[Route, ...],
    web_sockets: Dict[str, WS],
    event_handlers: Dict[Events, list],
    socket: SocketHeld,
    workers: Number,
) -> None:
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
    :param workers number: This is the name given to the process to identify the process
    """
