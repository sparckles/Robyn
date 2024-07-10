from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Callable
from robyn.argument_parser import Config
from robyn.dependency_injection import DependencyMap

from robyn.robyn import FunctionInfo

if TYPE_CHECKING:
    from robyn import Robyn

import logging

_logger = logging.getLogger(__name__)


class WebSocket:
    # should this be websocket router?
    """This is the python wrapper for the web socket that will be used here."""

    def __init__(self, robyn_object: "Robyn", endpoint: str, config: Config = Config(), dependencies: DependencyMap = DependencyMap()) -> None:
        self.robyn_object = robyn_object
        self.endpoint = endpoint
        self.methods = {}
        self.config = config
        self.dependencies = dependencies

    def on(self, type: str) -> Callable[..., None]:
        def inner(handler):
            if type not in ["connect", "close", "message"]:
                raise Exception(f"Socket method {type} does not exist")
            else:
                params = dict(inspect.signature(handler).parameters)
                num_params = len(params)
                is_async = asyncio.iscoroutinefunction(handler)

                injected_dependencies = self.dependencies.get_dependency_map(self)

            new_injected_dependencies = {}
            for dependency in injected_dependencies:
                if dependency in params:
                    new_injected_dependencies[dependency] = injected_dependencies[dependency]
                else:
                    _logger.debug(f"Dependency {dependency} is not used in the handler {handler.__name__}")

                self.methods[type] = FunctionInfo(handler, is_async, num_params, params, kwargs=new_injected_dependencies)
                self.robyn_object.add_web_socket(self.endpoint, self)

        return inner

    def inject(self, **kwargs):
        """
        Injects the dependencies for the route

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_router_dependency(self, **kwargs)

    def inject_global(self, **kwargs):
        """
        Injects the dependencies for the global routes
        Ideally, this function should be a global function

        :param kwargs dict: the dependencies to be injected
        """
        self.dependencies.add_global_dependency(**kwargs)
