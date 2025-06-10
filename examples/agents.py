#!/usr/bin/env python3
"""
Robyn AI Agents Example
=======================

This example demonstrates Robyn's AI capabilities including:
1. OpenAI-powered conversational agents with memory
2. REST API endpoints for chat interaction
3. Memory management for conversation history

Run with: python examples/agents.py

Features:
- Chat endpoint with persistent memory
- Memory retrieval and clearing endpoints
- Health check endpoint
"""

import os
from datetime import datetime

from robyn import Robyn
from robyn.ai import agent, memory, configure


app = Robyn(__file__)

# ============================================================================
# AI Agent Configuration
# ============================================================================

AGENT_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 500
}

# Global agent instance
ai_agent = None

async def setup_agent():
    """Initialize the AI agent with configuration"""
    global ai_agent
    
    if not AGENT_CONFIG["openai_api_key"]:
        print("⚠️  No OpenAI API key found. AI agent will not be available.")
        print("   Set OPENAI_API_KEY environment variable to enable chat.")
        return
    
    try:
        user_memory = memory(provider="inmemory", user_id="default_user")
        
        ai_config = configure(
            openai_api_key=AGENT_CONFIG["openai_api_key"],
            model=AGENT_CONFIG["model"],
            temperature=AGENT_CONFIG["temperature"],
            max_tokens=AGENT_CONFIG["max_tokens"]
        )
        
        ai_agent = agent(runner="simple", memory=user_memory, config=ai_config)
        print("✓ AI agent initialized successfully")
        
    except Exception as e:
        print(f"✗ Failed to initialize AI agent: {e}")
        ai_agent = None

@app.startup_handler
async def startup():
    """Setup agent on startup"""
    await setup_agent()




# ============================================================================
# AI Agent Endpoints
# ============================================================================

@app.post("/chat")
async def chat(request):
    """Chat with the AI agent"""
    if not ai_agent:
        return {"error": "AI agent not available. Set OPENAI_API_KEY environment variable."}
    
    try:
        data = request.json()
        query = data.get("query", "")
        use_history = data.get("history", True)
        
        if not query:
            return {"error": "Query is required"}
        
        result = await ai_agent.run(query, history=use_history)
        
        return {
            "query": query,
            "response": result.get("response", "No response generated"),
            "model": AGENT_CONFIG["model"]
        }
        
    except Exception as e:
        return {"error": f"Chat failed: {str(e)}"}

@app.get("/memory")
async def get_memory():
    """Get conversation memory"""
    if not ai_agent or not ai_agent.memory:
        return {"memory": [], "count": 0}
    
    try:
        memory_data = await ai_agent.memory.get()
        return {"memory": memory_data, "count": len(memory_data)}
    except Exception as e:
        return {"error": f"Memory retrieval failed: {str(e)}"}

@app.delete("/memory")
async def clear_memory():
    """Clear conversation memory"""
    if not ai_agent or not ai_agent.memory:
        return {"message": "No memory to clear"}
    
    try:
        await ai_agent.memory.clear()
        return {"message": "Memory cleared successfully"}
    except Exception as e:
        return {"error": f"Memory clear failed: {str(e)}"}

# ============================================================================
# Main Routes
# ============================================================================

@app.get("/")
def home():
    """AI Agent home page"""
    return {
        "name": "Robyn AI Agents Example",
        "description": "OpenAI-powered conversational agents with memory",
        "version": "1.0.0",
        "features": {
            "ai_agent": {
                "enabled": ai_agent is not None,
                "model": AGENT_CONFIG["model"] if ai_agent else None,
                "endpoints": ["/chat", "/memory"]
            }
        },
        "examples": {
            "chat": {
                "url": "POST /chat",
                "body": {"query": "Hello! What can you help me with?"}
            }
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_agent": "active" if ai_agent else "inactive"
    }

if __name__ == "__main__":
    print("🤖 Robyn AI Agents Example")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:8080")
    print(f"💬 Chat Endpoint: http://localhost:8080/chat")
    print(f"❤️  Health Check: http://localhost:8080/health")
    print()
    
    print("AI Agent:")
    if AGENT_CONFIG["openai_api_key"]:
        print(f"  ✓ Model: {AGENT_CONFIG['model']}")
        print("  ✓ Memory: In-memory storage")
        print("  ✓ Chat endpoint available")
    else:
        print("  ⚠️  Disabled (no OPENAI_API_KEY)")
    print()
    
    print("💬 Chat with the AI agent:")
    print("   curl -X POST http://localhost:8080/chat \\")
    print("   -H 'Content-Type: application/json' \\")
    print("   -d '{\"query\": \"Hello! What can you help me with?\"}'")
    print()
    print("🚀 Starting server...")
    
    app.start(port=8080)