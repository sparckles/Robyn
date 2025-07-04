"""
Server-Sent Events (SSE) Example for Robyn

This example demonstrates how to implement Server-Sent Events using Robyn,
similar to FastAPI's implementation. SSE allows real-time server-to-client
communication over a single HTTP connection.
"""

import time
import asyncio
from robyn import Robyn, SSE_Response, SSE_Message, html

app = Robyn(__file__)


@app.get("/")
def index(request):
    """Serve a simple HTML page to test SSE"""
    return html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Robyn SSE Example</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            #events { border: 1px solid #ccc; padding: 20px; height: 300px; overflow-y: auto; }
            .event { margin: 5px 0; padding: 5px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>Robyn Server-Sent Events Demo</h1>
        <div id="events"></div>
        <script>
            const eventSource = new EventSource('/events');
            const eventsDiv = document.getElementById('events');
            
            eventSource.onmessage = function(event) {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';
                eventDiv.textContent = event.data;
                eventsDiv.appendChild(eventDiv);
                eventsDiv.scrollTop = eventsDiv.scrollHeight;
            };
            
            eventSource.onerror = function(event) {
                console.error('SSE error:', event);
            };
        </script>
    </body>
    </html>
    """)


@app.get("/events")
def stream_events(request):
    """Basic SSE endpoint that sends a message every second"""
    
    def event_generator():
        """Generator function that yields SSE-formatted messages"""
        for i in range(10):
            yield SSE_Message(f"Message {i} - {time.strftime('%H:%M:%S')}", id=str(i))
            time.sleep(1)
        
        # Send a final message
        yield SSE_Message("Stream ended", event="end")
    
    return SSE_Response(event_generator())


@app.get("/events/json")
def stream_json_events(request):
    """SSE endpoint that sends JSON data"""
    import json
    
    def json_event_generator():
        """Generator that yields JSON data as SSE"""
        for i in range(5):
            data = {
                "id": i,
                "message": f"JSON message {i}",
                "timestamp": time.time(),
                "type": "notification"
            }
            yield SSE_Message(json.dumps(data), event="notification", id=str(i))
            time.sleep(2)
    
    return SSE_Response(json_event_generator())


@app.get("/events/named")
def stream_named_events(request):
    """SSE endpoint with named events"""
    
    def named_event_generator():
        """Generator that yields named SSE events"""
        events = [
            ("user_joined", "Alice joined the chat"),
            ("message", "Hello everyone!"),
            ("user_left", "Bob left the chat"),
            ("message", "How is everyone doing?"),
            ("user_joined", "Charlie joined the chat")
        ]
        
        for i, (event_type, message) in enumerate(events):
            yield SSE_Message(message, event=event_type, id=str(i))
            time.sleep(1.5)
    
    return SSE_Response(named_event_generator())


@app.get("/events/async")
async def stream_async_events(request):
    """Async SSE endpoint demonstrating async generators"""
    
    async def async_event_generator():
        """Async generator for SSE events"""
        for i in range(8):
            # Simulate async work
            await asyncio.sleep(0.5)
            yield SSE_Message(f"Async message {i} - {time.strftime('%H:%M:%S')}", event="async", id=str(i))
    
    return SSE_Response(async_event_generator())


@app.get("/events/heartbeat")
def stream_heartbeat(request):
    """SSE endpoint that sends heartbeat messages"""
    
    def heartbeat_generator():
        """Generator that sends heartbeat pings"""
        counter = 0
        while counter < 20:  # Send 20 heartbeats
            yield SSE_Message(f"heartbeat {counter}", event="heartbeat", id=str(counter))
            counter += 1
            time.sleep(0.5)
        
        yield SSE_Message("heartbeat ended", event="end")
    
    return SSE_Response(heartbeat_generator())


@app.get("/help")
def help_page(request):
    """Help page explaining available endpoints"""
    return html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Robyn SSE Help</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            code { background: #f4f4f4; padding: 2px 4px; }
        </style>
    </head>
    <body>
        <h1>Robyn SSE Example Endpoints</h1>
        
        <div class="endpoint">
            <h3><code>GET /</code></h3>
            <p>Main demo page with a live SSE client</p>
        </div>
        
        <div class="endpoint">
            <h3><code>GET /events</code></h3>
            <p>Basic SSE stream with 10 messages sent every second</p>
        </div>
        
        <div class="endpoint">
            <h3><code>GET /events/json</code></h3>
            <p>SSE stream sending JSON data every 2 seconds</p>
        </div>
        
        <div class="endpoint">
            <h3><code>GET /events/named</code></h3>
            <p>SSE stream with named events (user_joined, message, user_left)</p>
        </div>
        
        <div class="endpoint">
            <h3><code>GET /events/async</code></h3>
            <p>Async SSE stream demonstrating async generators</p>
        </div>
        
        <div class="endpoint">
            <h3><code>GET /events/heartbeat</code></h3>
            <p>Fast heartbeat stream sending messages every 0.5 seconds</p>
        </div>
        
        <p><strong>Usage:</strong> Use curl, browser EventSource API, or any SSE client to connect to these endpoints.</p>
        
        <h3>Example with curl:</h3>
        <pre><code>curl http://localhost:8080/events</code></pre>
        
        <h3>Example with JavaScript:</h3>
        <pre><code>const eventSource = new EventSource('/events');
eventSource.onmessage = function(event) {
    console.log('Received:', event.data);
};</code></pre>
    </body>
    </html>
    """)


if __name__ == "__main__":
    print("Starting Robyn SSE Example Server...")
    print("Visit http://localhost:8080/ for the main demo")
    print("Visit http://localhost:8080/help for endpoint documentation")
    app.start(host="0.0.0.0", port=8080)
