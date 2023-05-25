from __future__ import annotations

import asyncio
from inspect import signature
from typing import TYPE_CHECKING, Callable

from robyn.robyn import FunctionInfo
from websockets.sync.client import connect as sync_connect
from websockets import connect

if TYPE_CHECKING:
    from robyn import Robyn


class WS:
    """This is the python wrapper for the web socket that will be used here."""

    def __init__(self, robyn_object: "Robyn", endpoint: str) -> None:
        self.robyn_object = robyn_object
        self.endpoint = endpoint
        self.methods = {}
        self.url = f"ws://127.0.0.1:8080{endpoint}"

    def on(self, type: str) -> Callable[..., None]:
        def inner(handler):
            if type not in ["connect", "close", "message"]:
                raise Exception(f"Socket method {type} does not exist")
            else:
                self.methods[type] = FunctionInfo(
                    handler, self._is_async(handler), self._num_params(handler)
                )
                self.robyn_object.add_web_socket(self.endpoint, self)

        return inner

    def _num_params(self, handler):
        return len(signature(handler).parameters)

    def _is_async(self, handler):
        return asyncio.iscoroutinefunction(handler)

    def send(self, message: str) -> None:
        print("This is the url ", self.url)
        # making new connection each time
        # is very slow
        # expose sync_connect outside of this class
        with sync_connect(self.url) as websocket:
            websocket.send(message)

    def recv(self):
        with sync_connect(self.url) as websocket:
            return websocket.recv()

    async def send_async(self, message: str) -> None:
        async with connect(self.url) as websocket:
            await websocket.send(message)

    async def recv_async(self) -> str:
        async with connect(self.url) as websocket:
            return await websocket.recv()


__all__ = ["WS", "connect", "sync_connect"]
