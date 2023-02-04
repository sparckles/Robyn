from robyn import Robyn
from robyn.events import Events
from robyn.types import Header


def test_add_request_header():
    app = Robyn(__file__)
    app.add_request_header("server", "robyn")
    assert app.request_headers == [Header(key="server", val="robyn")]


def test_lifecycle_handlers():
    def mock_startup_handler():
        pass

    async def mock_shutdown_handler():
        pass

    app = Robyn(__file__)

    app.startup_handler(mock_startup_handler)
    assert Events.STARTUP in app.event_handlers
    startup = app.event_handlers[Events.STARTUP]
    assert startup.handler == mock_startup_handler
    assert startup.is_async is False
    assert startup.number_of_params == 0

    app.shutdown_handler(mock_shutdown_handler)
    assert Events.SHUTDOWN in app.event_handlers
    shutdown = app.event_handlers[Events.SHUTDOWN]
    assert shutdown.handler == mock_shutdown_handler
    assert shutdown.is_async is True
    assert shutdown.number_of_params == 0
