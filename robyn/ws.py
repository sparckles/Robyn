from __future__ import annotations

import asyncio
from inspect import signature
from typing import TYPE_CHECKING, Callable

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from robyn import Robyn


class WS:
    """This is the python wrapper for the web socket that will be used here.
    """
    def __init__(self, robyn_object: "Robyn", endpoint: str) -> None:
        self.robyn_object = robyn_object
        self.endpoint = endpoint
        self.methods = {}

    # (handler: Unknown) -> Failure[Exception] | None
    def on(self, type: str) -> Result[Callable[..., None], Exception]:
        def inner(handler):
            if type not in ["connect", "close", "message"]:
                return Failure(Exception(f"Socket method {type} does not exist"))
            else:
                self.methods[type] = (handler, self._is_async(handler), self._num_params(handler))
                self.robyn_object.add_web_socket(self.endpoint, self)

        return Success(inner)

    def _num_params(self, handler):
        return len(signature(handler).parameters)

    def _is_async(self, handler):
        return asyncio.iscoroutinefunction(handler)

