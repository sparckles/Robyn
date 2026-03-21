from __future__ import annotations

import asyncio
import inspect
import logging

import orjson

from robyn._param_utils import QueryParamValidationError, resolve_individual_params
from robyn.robyn import FunctionInfo, QueryParams, WebSocketConnector

_logger = logging.getLogger(__name__)


class WebSocketDisconnect(Exception):
    """Exception raised when a WebSocket connection is disconnected."""

    def __init__(self, code: int = 1000, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket disconnected with code {code}: {reason}")


class WebSocketAdapter:
    """
    Modern WebSocket interface backed by Rust channels.

    Wraps a WebSocketConnector and a Rust WebSocketChannel to provide
    a clean async API for WebSocket handlers.
    """

    def __init__(self, websocket_connector: WebSocketConnector, channel=None):
        self._connector = websocket_connector
        self._channel = channel

    async def receive_text(self) -> str:
        """Receive the next text message. Blocks until a message arrives.
        Raises WebSocketDisconnect when the connection is closed."""
        if self._channel is None:
            raise WebSocketDisconnect(reason="No message channel available")
        result = await self._channel.receive()
        if result is None:
            raise WebSocketDisconnect()
        return result

    async def receive_bytes(self) -> bytes:
        """Receive binary data (decoded from text)."""
        text = await self.receive_text()
        return text.encode("utf-8")

    async def receive_json(self):
        """Receive and decode JSON data.
        Raises WebSocketDisconnect when the connection is closed."""
        text = await self.receive_text()
        return orjson.loads(text)

    async def send_text(self, data: str):
        """Send text data to this WebSocket client."""
        await self._connector.async_send_to(self._connector.id, data)

    async def send_bytes(self, data: bytes):
        """Send binary data (as text) to this WebSocket client."""
        await self._connector.async_send_to(self._connector.id, data.decode("utf-8"))

    async def send_json(self, data):
        """Send JSON data to this WebSocket client."""
        await self.send_text(orjson.dumps(data).decode())

    async def broadcast(self, data: str):
        """Broadcast text data to all connected WebSocket clients on this endpoint."""
        await self._connector.async_broadcast(data)

    async def close(self):
        """Close the WebSocket connection."""
        self._connector.close()

    @property
    def id(self) -> str:
        """WebSocket connection ID."""
        return self._connector.id

    @property
    def query_params(self):
        """Access query parameters from the connection URL."""
        return self._connector.query_params


# Global storage for connection state (per-connection queues and tasks)
_connection_tasks: dict[str, asyncio.Task] = {}


def create_websocket_decorator(app_instance):
    """
    Factory function to create a websocket decorator for an app instance.
    Returns a decorator that registers a modern WebSocket endpoint
    backed by Rust channels.
    """

    def websocket(endpoint: str):
        """
        Modern WebSocket decorator.

        Usage:
            @app.websocket("/ws")
            async def handler(websocket):
                while True:
                    msg = await websocket.receive_text()
                    await websocket.send_text(f"Echo: {msg}")

            @handler.on_connect
            def on_connect(websocket):
                return "Welcome!"

            @handler.on_close
            def on_close(websocket):
                return "Goodbye"
        """

        def decorator(handler):
            _on_connect_fn = None
            _on_close_fn = None

            def _resolve_ws_params(func_params, adapter):
                """
                Resolve all handler params beyond the first positional (websocket).

                Handles:
                  - global_dependencies / router_dependencies (DI)
                  - query_params (whole QueryParams object, by name or type annotation)
                  - individual query params (everything else, with type coercion)
                """
                injected = app_instance.dependencies.get_dependency_map(app_instance)
                resolved = {}
                unresolved = {}

                for idx, (param_name, param) in enumerate(func_params.items()):
                    # Skip the websocket adapter (first positional arg, passed separately)
                    if idx == 0 or param.annotation is WebSocketAdapter:
                        continue

                    # DI: global_dependencies
                    if param_name == "global_dependencies":
                        resolved[param_name] = injected.get("global_dependencies", {})
                        continue

                    # DI: router_dependencies
                    if param_name == "router_dependencies":
                        resolved[param_name] = injected.get("router_dependencies", {})
                        continue

                    # Whole QueryParams object (by type annotation or reserved name)
                    if param.annotation is QueryParams or param_name == "query_params":
                        resolved[param_name] = adapter.query_params
                        continue

                    # Everything else: individual query param
                    unresolved[param_name] = param

                if unresolved:
                    individual = resolve_individual_params(
                        unresolved,
                        adapter.query_params,
                        path_params=None,  # WebSocket has no path params yet
                        route_param_names=set(),
                    )
                    resolved.update(individual)

                return resolved

            # --- Connect handler (called by Rust on connection open) ---
            async def connect_handler(ws):
                """Internal connect handler called by Rust.
                Creates the adapter, starts the user's handler task,
                and calls the user's on_connect callback."""
                conn_id = ws.id
                channel = ws.message_channel

                # Create the adapter with the Rust channel
                adapter = WebSocketAdapter(ws, channel)

                # Build resolved kwargs for the main handler
                try:
                    handler_params = inspect.signature(handler).parameters
                    handler_kwargs = _resolve_ws_params(handler_params, adapter)
                except QueryParamValidationError as e:
                    _logger.warning("WebSocket connection rejected for %s: %s", endpoint, e.detail)
                    return f"Error: {e.detail}"

                # Start the user's handler as a long-running asyncio task
                async def _run_handler():
                    try:
                        await handler(adapter, **handler_kwargs)
                    except WebSocketDisconnect:
                        pass
                    except ConnectionError:
                        _logger.debug("Connection lost in WebSocket handler for %s", endpoint, exc_info=True)
                    except Exception:
                        _logger.exception("Error in WebSocket handler for %s", endpoint)
                    finally:
                        _connection_tasks.pop(conn_id, None)

                task = asyncio.create_task(_run_handler())
                _connection_tasks[conn_id] = task

                # Call user's on_connect if defined
                if _on_connect_fn is not None:
                    connect_adapter = WebSocketAdapter(ws, channel)
                    try:
                        connect_params = inspect.signature(_on_connect_fn).parameters
                        connect_kwargs = _resolve_ws_params(connect_params, connect_adapter)
                    except QueryParamValidationError as e:
                        _logger.warning("WebSocket on_connect rejected for %s: %s", endpoint, e.detail)
                        task = _connection_tasks.pop(conn_id, None)
                        if task is not None and not task.done():
                            task.cancel()
                        return f"Error: {e.detail}"
                    if asyncio.iscoroutinefunction(_on_connect_fn):
                        result = await _on_connect_fn(connect_adapter, **connect_kwargs)
                    else:
                        result = _on_connect_fn(connect_adapter, **connect_kwargs)
                    return result

                return None

            # --- Message handler (dummy for new-style; Rust pushes to channel instead) ---
            async def message_handler(ws, msg):
                """Dummy message handler. In channel mode, Rust pushes messages
                directly to the channel and never calls this."""
                return None

            # --- Close handler (called by Rust on connection close) ---
            async def close_handler(ws):
                """Internal close handler called by Rust.
                Waits for the handler task to finish and calls on_close."""
                conn_id = ws.id

                # Wait for the handler task to finish (it should exit because
                # the channel was closed by Rust, triggering WebSocketDisconnect)
                task = _connection_tasks.pop(conn_id, None)
                if task is not None:
                    try:
                        await asyncio.wait_for(task, timeout=5.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        if not task.done():
                            task.cancel()
                    except Exception:
                        _logger.debug("Unexpected error while awaiting handler task for %s", conn_id, exc_info=True)
                        if not task.done():
                            task.cancel()

                # Call user's on_close if defined
                if _on_close_fn is not None:
                    close_adapter = WebSocketAdapter(ws, None)
                    try:
                        close_params = inspect.signature(_on_close_fn).parameters
                        close_kwargs = _resolve_ws_params(close_params, close_adapter)
                    except QueryParamValidationError as e:
                        _logger.warning("WebSocket on_close param error for %s: %s", endpoint, e.detail)
                        return None
                    if asyncio.iscoroutinefunction(_on_close_fn):
                        result = await _on_close_fn(close_adapter, **close_kwargs)
                    else:
                        result = _on_close_fn(close_adapter, **close_kwargs)
                    return result

                return None

            # --- Build FunctionInfo objects for Rust ---
            handlers = {}

            # Connect handler FunctionInfo
            connect_params = dict(inspect.signature(connect_handler).parameters)
            handlers["connect"] = FunctionInfo(
                connect_handler,
                True,  # is_async
                len(connect_params),
                connect_params,
                {},  # no kwargs needed - DI handled in Python
            )

            # Message handler FunctionInfo (dummy, won't be called in channel mode)
            message_params = dict(inspect.signature(message_handler).parameters)
            handlers["message"] = FunctionInfo(
                message_handler,
                True,
                len(message_params),
                message_params,
                {},
            )

            # Close handler FunctionInfo
            close_params = dict(inspect.signature(close_handler).parameters)
            handlers["close"] = FunctionInfo(
                close_handler,
                True,
                len(close_params),
                close_params,
                {},
            )

            # --- Decorator methods for on_connect / on_close ---
            def add_on_connect(connect_fn):
                nonlocal _on_connect_fn
                _on_connect_fn = connect_fn
                return connect_fn

            def add_on_close(close_fn):
                nonlocal _on_close_fn
                _on_close_fn = close_fn
                return close_fn

            handler.on_connect = add_on_connect
            handler.on_close = add_on_close

            # Register with the app
            app_instance.add_web_socket(endpoint, handlers)

            return handler

        return decorator

    return websocket
