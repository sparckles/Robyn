"""
Example Robyn AI application demonstrating agent and memory functionality
"""

from robyn import Robyn
from robyn.ai import agent, memory
from typing import Optional

app = Robyn(__file__)

# Create memory instance for guest user
mem = memory(provider="mem0", user_id="guest")

# Create agent with simple runner and memory
chat = agent(
    runner="simple",
    memory=mem
)


@app.get("/")
async def hello():
    """Simple hello endpoint"""
    return {"message": "Hello from Robyn AI! Try /chat?q=your_question"}

@app.get("/chat")
async def ask(request):
    """
    Chat endpoint with AI agent
    
    Query parameters:
    - q: The question to ask the agent
    - history: Whether to include conversation history (default: False)
    """
    try:
        query_data = request.query_params.to_dict()
        q = query_data.get("q", [""])[0] if query_data.get("q") else ""
        history = query_data.get("history", ["false"])[0].lower() == "true"
        
        if not q:
            return {"error": "Query parameter 'q' is required"}
        
        result = await chat.run(q, history=history)
        return {
            "query": q,
            "response": result.get("response", "No response"),
            "history_included": history
        }
    except Exception as e:
        return {
            "error": str(e),
            "query": q if 'q' in locals() else "unknown"
        }

@app.post("/chat")
async def chat_post(request):
    """
    POST endpoint for chat with JSON body
    
    Expected JSON body:
    {
        "query": "your question",
        "history": true/false (optional)
    }
    """
    try:
        data = request.json()
        query = data.get("query", "")
        history = data.get("history", False)
        
        if not query:
            return {"error": "Query is required"}
        
        result = await chat.run(query, history=history)
        return {
            "query": query,
            "response": result.get("response", "No response"),
            "history_included": history
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@app.get("/memory")
async def get_memory():
    """Get all memory for the current user"""
    try:
        memories = await mem.get()
        return {
            "memories": memories,
            "count": len(memories)
        }
    except Exception as e:
        return {"error": str(e)}

@app.delete("/memory")
async def clear_memory():
    """Clear all memory for the current user"""
    try:
        await mem.clear()
        return {"message": "Memory cleared successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/memory")
async def add_memory(request):
    """
    Add a message to memory
    
    Expected JSON body:
    {
        "message": "your message",
        "metadata": {} (optional)
    }
    """
    try:
        data = request.json()
        message = data.get("message", "")
        metadata = data.get("metadata", {})
        
        if not message:
            return {"error": "Message is required"}
        
        await mem.add(message, metadata)
        return {"message": "Added to memory successfully"}
    except Exception as e:
        return {"error": str(e)}

# Simple form handler
@app.post("/submit")
async def handle_form(request):
    """Simple form handler example"""
    try:
        data = request.form_data()
        name = data.get("name", "")
        email = data.get("email", "")
        
        if not name or not email:
            return {"error": "Name and email are required"}
        
        return {"message": f"Received form from {name} ({email})"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.start(host="127.0.0.1", port=8080)
