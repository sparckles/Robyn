
import asyncio
from websockets.sync.client import connect

def hello():
    with connect("ws://localhost:8080/web_socket") as websocket:
        websocket.send("Hello world!")
        message = websocket.recv()
        print(f"Received: {message}")
        for i in range(10):
            import time
            time.sleep(1)
            websocket.send(f"Hello world! {i}")
            message = websocket.recv()
            print(f"Received: {message}")

hello()
