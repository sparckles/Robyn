#!/usr/bin/env python3
"""
Example showing how to use the WebSocket decorator with on_connect and on_close handlers.
"""

from robyn import Robyn, WebSocketDisconnect

app = Robyn(__file__)

# Define the main WebSocket handler
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "close":
                break
            else:
                await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

# Now you can add on_connect and on_close handlers to websocket_endpoint
@websocket_endpoint.on_connect
async def on_connect(websocket):
    await websocket.send_text("Welcome! You are now connected.")
    print("New client connected")

@websocket_endpoint.on_close  
async def on_close(websocket):
    print("Client disconnected from WebSocket")

# You can also add handlers programmatically:
def another_connect_handler(websocket):
    print("Another connect handler called")

# This would override the previous on_connect handler
# websocket_endpoint.on_connect(another_connect_handler)

@app.get("/")
def index():
    return """
    <h1>WebSocket Test</h1>
    <p>Connect to: ws://localhost:8080/ws</p>
    <p>Send 'ping' to get 'pong' response</p>
    <p>Send 'close' to disconnect</p>
    """

if __name__ == "__main__":
    print("Starting WebSocket server...")
    print("Connect to: ws://localhost:8080/ws")
    app.start(host="0.0.0.0", port=8080)