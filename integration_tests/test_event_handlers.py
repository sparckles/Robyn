import logging


def test_startup_event(session, caplog):
    with caplog.at_level(logging.INFO):
        assert "Starting up" in caplog.text


def test_shutdown_event(session, caplog):
    with caplog.at_level(logging.INFO):
        assert "Shutting down" in caplog.text
