import asyncio
import inspect
import logging
from typing import TYPE_CHECKING, Callable

import orjson

from robyn.argument_parser import Config
from robyn.dependency_injection import DependencyMap
from robyn.robyn import FunctionInfo, WebSocketConnector

if TYPE_CHECKING:
    from robyn import Robyn

_logger = logging.getLogger(__name__)


class WebSocketDisconnect(Exception):
    """Exception raised when a WebSocket connection is disconnected."""
    
    def __init__(self, code: int = 1000, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket disconnected with code {code}: {reason}")


class WebSocketAdapter:
    """
    Adapter class that provides a modern WebSocket interface
    wrapping Robyn's WebSocketConnector for compatibility.
    """
    
    def __init__(self, websocket_connector: WebSocketConnector, message: str = None):
        self._connector = websocket_connector
        self._message = message
    
    async def close(self, code: int = 1000):
        """Close the WebSocket connection"""
        self._connector.close()
    
    async def send_text(self, data: str):
        """Send text data to the WebSocket"""
        await self._connector.async_send_to(self._connector.id, data)
    
    async def send_bytes(self, data: bytes):
        """Send binary data to the WebSocket"""
        await self._connector.async_send_to(self._connector.id, data.decode('utf-8'))
    
    async def receive_text(self) -> str:
        """Receive text data from the WebSocket"""
        if self._message is not None:
            msg = self._message
            self._message = None  # Consume the message
            return msg
        # Note: In a real implementation, this would need to handle the message queue
        # For now, we return the current message if available
        return ""
    
    async def receive_bytes(self) -> bytes:
        """Receive binary data from the WebSocket"""
        text = await self.receive_text()
        return text.encode('utf-8')
    
    async def send_json(self, data):
        """Send JSON data to the WebSocket"""
        await self.send_text(orjson.dumps(data).decode())
    
    async def receive_json(self):
        """Receive JSON data from the WebSocket"""
        text = await self.receive_text()
        return orjson.loads(text) if text else None
    
    async def broadcast(self, data: str):
        """Broadcast data to all connected WebSocket clients"""
        await self._connector.async_broadcast(data)
    
    @property
    def query_params(self):
        """Access query parameters"""
        return self._connector.query_params
    
    @property
    def path_params(self):
        """Access path parameters"""
        return getattr(self._connector, 'path_params', {})
    
    @property
    def headers(self):
        """Access request headers"""
        return getattr(self._connector, 'headers', {})
    
    @property
    def client(self):
        """Client information"""
        return getattr(self._connector, 'client', None)
    
    @property
    def id(self):
        """WebSocket connection ID"""
        return self._connector.id


def create_websocket_decorator(app_instance):
    """
    Factory function to create a websocket decorator for an app instance.
    This allows access to the app's dependencies and web_socket_router.
    """
    def websocket(endpoint: str):
        """
        Modern WebSocket decorator that accepts a single handler function.
        The handler function receives a WebSocket object and can optionally have on_connect and on_close callbacks.
        
        Usage:
        @app.websocket("/ws")
        async def websocket_endpoint(websocket):
            await websocket.accept()
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
        
        # With optional callbacks:
        @websocket_endpoint.on_connect
        async def on_connect(websocket):
            await websocket.send_text("Connected!")
            
        @websocket_endpoint.on_close  
        async def on_close(websocket):
            print("Disconnected")
        """
        def decorator(handler):
            # Dictionary to store handlers for this WebSocket endpoint
            handlers = {}
            
            # Create the main message handler
            async def message_handler(websocket_connector, msg, *args, **kwargs):
                # Convert WebSocketConnector to modern WebSocket interface
                websocket_adapter = WebSocketAdapter(websocket_connector, msg)
                try:
                    # Call the user's handler
                    result = await handler(websocket_adapter)
                    return result if result is not None else ""
                except WebSocketDisconnect:
                    # Handle disconnections gracefully
                    return ""
                except Exception as e:
                    # Handle other connection errors gracefully
                    if "connection closed" in str(e).lower() or "websocket" in str(e).lower():
                        return ""
                    raise e
            
            # Create FunctionInfo for the message handler
            params = dict(inspect.signature(message_handler).parameters)
            num_params = len(params)
            is_async = asyncio.iscoroutinefunction(message_handler)
            injected_dependencies = app_instance.dependencies.get_dependency_map(app_instance)
            
            # Filter dependencies to only include reserved parameters that exist in handler
            filtered_dependencies = {}
            if "global_dependencies" in params:
                filtered_dependencies["global_dependencies"] = injected_dependencies.get("global_dependencies", {})
            if "router_dependencies" in params:
                filtered_dependencies["router_dependencies"] = injected_dependencies.get("router_dependencies", {})
            
            handlers["message"] = FunctionInfo(message_handler, is_async, num_params, params, filtered_dependencies)
            
            # Add methods to the handler to allow attaching on_connect and on_close
            def add_on_connect(connect_handler):
                def connect_wrapper(websocket_connector, *args, **kwargs):
                    websocket_adapter = WebSocketAdapter(websocket_connector)
                    if asyncio.iscoroutinefunction(connect_handler):
                        return asyncio.create_task(connect_handler(websocket_adapter))
                    return connect_handler(websocket_adapter)
                
                # Create FunctionInfo for connect handler
                connect_params = dict(inspect.signature(connect_handler).parameters)  # Use original handler params, not wrapper
                connect_num_params = len(connect_params)
                connect_is_async = asyncio.iscoroutinefunction(connect_wrapper)
                
                # Filter dependencies for connect handler - only reserved parameters
                filtered_connect_deps = {}
                if "global_dependencies" in connect_params:
                    filtered_connect_deps["global_dependencies"] = injected_dependencies.get("global_dependencies", {})
                if "router_dependencies" in connect_params:
                    filtered_connect_deps["router_dependencies"] = injected_dependencies.get("router_dependencies", {})
                        
                handlers["connect"] = FunctionInfo(connect_wrapper, connect_is_async, connect_num_params, connect_params, filtered_connect_deps)
                return connect_handler
            
            def add_on_close(close_handler):
                def close_wrapper(websocket_connector, *args, **kwargs):
                    websocket_adapter = WebSocketAdapter(websocket_connector)
                    if asyncio.iscoroutinefunction(close_handler):
                        return asyncio.create_task(close_handler(websocket_adapter))
                    return close_handler(websocket_adapter)
                
                # Create FunctionInfo for close handler
                close_params = dict(inspect.signature(close_handler).parameters)  # Use original handler params, not wrapper
                close_num_params = len(close_params)
                close_is_async = asyncio.iscoroutinefunction(close_wrapper)
                
                # Filter dependencies for close handler - only reserved parameters
                filtered_close_deps = {}
                if "global_dependencies" in close_params:
                    filtered_close_deps["global_dependencies"] = injected_dependencies.get("global_dependencies", {})
                if "router_dependencies" in close_params:
                    filtered_close_deps["router_dependencies"] = injected_dependencies.get("router_dependencies", {})
                        
                handlers["close"] = FunctionInfo(close_wrapper, close_is_async, close_num_params, close_params, filtered_close_deps)
                return close_handler
            
            # Attach methods to the handler function
            handler.on_connect = add_on_connect
            handler.on_close = add_on_close
            handler._ws_handlers = handlers  # Store reference to handlers dict
            
            # Add the WebSocket to the router
            app_instance.add_web_socket(endpoint, handlers)
            return handler
        
        return decorator
    
    return websocket


class WebSocket:
    """Legacy WebSocket class for backward compatibility."""

    def __init__(self, robyn_object: "Robyn", endpoint: str, config: Config = Config(), dependencies: DependencyMap = DependencyMap()) -> None:
        self.robyn_object = robyn_object
        self.endpoint = endpoint
        self.methods: dict = {}
        self.config = config
        self.dependencies = dependencies

    def on(self, type: str) -> Callable[..., None]:
        def inner(handler):
            if type not in ["connect", "close", "message"]:
                raise Exception(f"Socket method {type} does not exist")

            params = dict(inspect.signature(handler).parameters)
            num_params = len(params)
            is_async = asyncio.iscoroutinefunction(handler)

            injected_dependencies = self.dependencies.get_dependency_map(self)

            # Filter dependencies to only include reserved parameters that exist in handler
            new_injected_dependencies = {}
            if "global_dependencies" in params:
                new_injected_dependencies["global_dependencies"] = injected_dependencies.get("global_dependencies", {})
            if "router_dependencies" in params:
                new_injected_dependencies["router_dependencies"] = injected_dependencies.get("router_dependencies", {})

            self.methods[type] = FunctionInfo(handler, is_async, num_params, params, new_injected_dependencies)

            return handler

        return inner