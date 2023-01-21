from websocket import create_connection

BASE_URL = "ws://127.0.0.1:8080"


def test_web_socket(session):
    ws = create_connection(f"{BASE_URL}/web_socket")
    assert ws.recv() == "Hello world, from ws"
    ws.send("My name is?")
    assert ws.recv() == "Whaaat??"
    ws.send("My name is?")
    assert ws.recv() == "Whooo??"
    ws.send("My name is?")
    assert ws.recv() == "*chika* *chika* Slim Shady."
