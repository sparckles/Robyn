import json

from websocket import create_connection
import pytest

BASE_URL = "ws://127.0.0.1:8080"


@pytest.mark.benchmark
def test_web_socket(session):
    ws = create_connection(f"{BASE_URL}/web_socket")
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
