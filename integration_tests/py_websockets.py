
import asyncio
from websockets.sync.client import connect


def hello():
    with connect("ws://localhost:8080/web_socket") as websocket:
        for i in range(10):
            websocket.send(f"Hello world! {i}")
            message = websocket.recv()
            print(f"Received: {message}")

hello()
