from robyn import Robyn
from robyn.ai import agent, memory
from typing import Optional

app = Robyn(__file__)

# Memory + Agent
mem = memory(provider="mem0", user_id="guest")

chat = agent(
    runner="langgraph",
    memory=mem
)

# Typed query parameters (FastAPI-style)
@app.get("/chat")
async def ask(request):
    """Chat endpoint with query parameters"""
    query_params = request.query_params.to_dict()
    q = query_params.get("q", [""])[0] if query_params.get("q") else ""
    history_param = query_params.get("history", ["false"])[0]
    history = history_param.lower() in ["true", "1", "yes"]
    
    if not q:
        return {"error": "Query parameter 'q' is required"}
    
    result = await chat.run(q, history=history)
    return result

@app.get("/")
async def hello():
    return {"message": "Hello from Robyn, now with memory."}

# Simple form handler
@app.post("/submit")
async def handle_form(request):
    """Form handler that accepts name and email"""
    try:
        # Try JSON first, then form data
        try:
            data = request.json()
            name = data.get("name", "")
            email = data.get("email", "")
        except:
            form_data = request.form_data()
            name = form_data.get("name", "")
            email = form_data.get("email", "")
        
        if not name or not email:
            return {"error": "Both name and email are required"}
            
        return {"message": f"Received form from {name} ({email})"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.start(host="127.0.0.1", port=8080)