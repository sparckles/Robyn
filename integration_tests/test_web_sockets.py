import json

import pytest
from websocket import create_connection

BASE_URL = "ws://127.0.0.1:8080"


@pytest.mark.benchmark
def test_web_socket_raw_benchmark(session):
    ws = create_connection(f"{BASE_URL}/web_socket?one=hi&two=hello")
    assert ws.recv() == "Hello world, from ws"

    ws.send("My name is?")
    # Messages may arrive in any order due to WebSocket broadcast behavior
    received = sorted([ws.recv() for _ in range(3)])
    expected = sorted(["This is a broadcast message", "This is a message to self", "Whaaat??"])
    assert received == expected

    ws.send("My name is?")
    assert ws.recv() == "Whooo??"

    ws.send("My name is?")
    received = sorted([ws.recv() for _ in range(3)])
    expected = sorted(["hi", "hello", "*chika* *chika* Slim Shady."])
    assert received == expected

    # this will close the connection
    ws.send("test")
    assert ws.recv() == "Connection closed"


def test_web_socket_json(session):
    """
    Not using this as the benchmark test since this involves JSON marshalling/unmarshalling
    which pollutes the benchmark measurement.
    """
    ws = create_connection(f"{BASE_URL}/web_socket_json")
    assert ws.recv() == "Hello world, from ws"

    msg = "My name is?"

    ws.send(msg)
    resp = json.loads(ws.recv())
    assert resp["resp"] == "Whaaat??"
    assert resp["msg"] == msg

    ws.send(msg)
    resp = json.loads(ws.recv())
    assert resp["resp"] == "Whooo??"
    assert resp["msg"] == msg

    ws.send(msg)
    resp = json.loads(ws.recv())
    assert resp["resp"] == "*chika* *chika* Slim Shady."
    assert resp["msg"] == msg


def test_websocket_di(session):
    """Test dependency injection in all WebSocket phases: connect, handler, and close."""

    ws = create_connection(f"{BASE_URL}/web_socket_di")

    # 1. on_connect should receive both global and router dependencies
    assert ws.recv() == "connect: GLOBAL DEPENDENCY ROUTER DEPENDENCY"

    # 2. Main handler should also receive both dependencies when processing messages
    ws.send("test")
    assert ws.recv() == "handler: GLOBAL DEPENDENCY ROUTER DEPENDENCY"

    # Send another message to confirm DI is stable across multiple messages
    ws.send("test again")
    assert ws.recv() == "handler: GLOBAL DEPENDENCY ROUTER DEPENDENCY"

    ws.close()


def test_websocket_empty_returns(session):
    """Test that WebSocket handlers can return nothing without causing errors"""
    ws = create_connection(f"{BASE_URL}/web_socket_empty_returns")

    # Connect handler returns None - no message should be received on connection
    # We need to send a message to verify the connection is still active
    ws.send("test message")

    # Message handler returns None - no response should be sent
    # The socket should still be open, not crashed
    # We can verify this by closing the connection gracefully
    ws.close()
    # If we got here without exceptions, the test passed
