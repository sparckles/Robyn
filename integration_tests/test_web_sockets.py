from websockets import connect
import asyncio

BASE_URL = "ws://127.0.0.1:5000"


def test_web_socket(session):
    async def start_ws(uri):
        async with connect(uri) as websocket:
            assert await websocket.recv() == "Hello world, from ws"
            await websocket.send("My name is?")
            assert await websocket.recv() == "Whaaat??"
            await websocket.send("My name is?")
            assert await websocket.recv() == "Whooo??"
            await websocket.send("My name is?")
            assert await websocket.recv() == "*chika* *chika* Slim Shady."

    asyncio.run(start_ws(f"{BASE_URL}/web_socket"))
