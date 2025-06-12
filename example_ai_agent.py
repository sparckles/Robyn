#!/usr/bin/env python3
"""
Example demonstrating Robyn's built-in AI agent and memory system.
Extensible design with in-memory storage and OpenAI agent implementation.
"""

import asyncio
import os
from robyn import Robyn
from robyn.ai import agent, memory, configure

# Initialize Robyn app
app = Robyn(__file__)

# Agent configuration with extensible design
AGENT_CONFIG = {
    "runner": "simple",  # SimpleRunner now has OpenAI integration
    "memory_provider": "inmemory",
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000,
    "debug": True
}

# Global agent instance
ai_agent = None

async def setup_agent():
    """Initialize the AI agent with configuration"""
    global ai_agent
    
    # Check if OpenAI key is available
    if AGENT_CONFIG["openai_api_key"] == "your-openai-api-key-here":
        print("✗ No OpenAI API key provided. Agent will not be initialized.")
        print("  Set OPENAI_API_KEY environment variable to use the AI agent.")
        return
    
    try:
        # Create memory instance
        user_memory = memory(
            provider=AGENT_CONFIG["memory_provider"],
            user_id="default_user"
        )
        
        # Create agent configuration
        ai_config = configure(
            openai_api_key=AGENT_CONFIG["openai_api_key"],
            model=AGENT_CONFIG["model"],
            temperature=AGENT_CONFIG["temperature"],
            max_tokens=AGENT_CONFIG["max_tokens"],
            debug=AGENT_CONFIG["debug"]
        )
        
        # Create agent with memory and configuration
        ai_agent = agent(
            runner=AGENT_CONFIG["runner"],
            memory=user_memory,
            config=ai_config
        )
        
        print("✓ AI agent initialized successfully")
        
    except Exception as e:
        print(f"✗ Failed to initialize AI agent: {e}")
        ai_agent = None

@app.startup_handler
async def startup():
    """Setup agent on startup"""
    await setup_agent()
    print("🚀 AI system ready!")

@app.get("/")
async def home():
    """Home page with API information"""
    return {
        "message": "Robyn AI Agent - OpenAI Integration",
        "config": {
            "runner": AGENT_CONFIG["runner"],
            "memory_provider": AGENT_CONFIG["memory_provider"],
            "model": AGENT_CONFIG["model"],
            "has_openai_key": bool(AGENT_CONFIG["openai_api_key"])
        },
        "endpoints": {
            "/chat": "POST - Chat with the AI agent",
            "/memory": "GET - View conversation memory",
            "/memory": "DELETE - Clear conversation memory",
            "/config": "GET - View current configuration"
        }
    }

@app.get("/config")
async def get_config():
    """Get current agent configuration"""
    return {
        "runner": AGENT_CONFIG["runner"],
        "memory_provider": AGENT_CONFIG["memory_provider"],
        "model": AGENT_CONFIG["model"],
        "temperature": AGENT_CONFIG["temperature"],
        "max_tokens": AGENT_CONFIG["max_tokens"],
        "debug": AGENT_CONFIG["debug"],
        "has_openai_key": bool(AGENT_CONFIG["openai_api_key"])
    }

@app.post("/chat")
async def chat(request):
    """Chat with the AI agent"""
    if not ai_agent:
        return {"error": "AI agent not initialized"}
    
    try:
        data = request.json()
        query = data.get("query", "")
        use_history = data.get("history", True)
        
        if not query:
            return {"error": "Query is required"}
        
        # Run the agent
        result = await ai_agent.run(query, history=use_history)
        
        return {
            "query": query,
            "response": result.get("response", "No response generated"),
            "metadata": result.get("metadata", {}),
            "config": {
                "runner": AGENT_CONFIG["runner"],
                "model": AGENT_CONFIG["model"]
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to process query: {str(e)}"}

@app.get("/memory")
async def get_memory():
    """Get conversation memory"""
    if not ai_agent or not ai_agent.memory:
        return {"memory": None}
    
    try:
        memory_data = await ai_agent.memory.get()
        return {
            "memory": memory_data,
            "count": len(memory_data)
        }
        
    except Exception as e:
        return {"error": f"Failed to retrieve memory: {str(e)}"}, 500

@app.delete("/memory")
async def clear_memory():
    """Clear conversation memory"""
    if not ai_agent or not ai_agent.memory:
        return {"message": "No memory to clear"}
    
    try:
        await ai_agent.memory.clear()
        return {"message": "Memory cleared successfully"}
        
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}

@app.post("/config")
async def update_config(request):
    """Update agent configuration (requires restart)"""
    try:
        data = request.json()
        
        # Update configuration
        for key, value in data.items():
            if key in AGENT_CONFIG:
                AGENT_CONFIG[key] = value
        
        return {
            "message": "Configuration updated. Restart required for changes to take effect.",
            "updated_config": AGENT_CONFIG
        }
        
    except Exception as e:
        return {"error": f"Failed to update config: {str(e)}"}, 500

# Example usage functions
async def example_usage():
    """Demonstrate the AI system capabilities"""
    print("\n🧪 Running example usage scenarios...\n")
    
    # Skip examples if no OpenAI key
    if AGENT_CONFIG["openai_api_key"] != "":
        print("Skipping examples - OpenAI API key required")
        print("Set OPENAI_API_KEY environment variable to run examples")
        return
    
    # Example 1: Basic chat
    print("1. Basic AI conversation:")
    user_memory = memory(provider="inmemory", user_id="example_user")
    
    config = configure(
        openai_api_key=AGENT_CONFIG["openai_api_key"],
        model=AGENT_CONFIG["model"],
        temperature=0.7,
        debug=True
    )
    demo_agent = agent(runner="simple", memory=user_memory, config=config)
    print("   Using OpenAI integration")
    
    # Chat examples
    queries = [
        "Hello! What can you help me with?",
        "What's 25 * 4?",
        "Can you remember what we talked about?"
    ]
    
    try:
        for query in queries:
            result = await demo_agent.run(query, history=True)
            print(f"   Q: {query}")
            print(f"   A: {result['response']}")
            print()
        
        # Example 2: Memory persistence
        print("2. Memory contents:")
        memory_data = await user_memory.get()
        for i, item in enumerate(memory_data, 1):
            print(f"   {i}. {item.get('message', item)}")
        print()
        
        # Example 3: Configuration example
        print("3. Agent with custom configuration:")
        
        custom_config = configure(
            openai_api_key=AGENT_CONFIG["openai_api_key"],
            model="gpt-4o",
            temperature=0.7,
            debug=True
        )
        
        custom_memory = memory(provider="inmemory", user_id="custom_user")
        custom_agent = agent("simple", custom_memory, custom_config)
        
        test_query = "Explain what Robyn framework does"
        result = await custom_agent.run(test_query)
        
        print(f"   Query: {test_query}")
        print(f"   Response: {result['response']}")
        print(f"   Runner type: {result.get('metadata', {}).get('runner_type', 'unknown')}")
        print()
        
    except Exception as e:
        print(f"   Error running examples: {e}")
        print()

if __name__ == "__main__":
    print("🤖 Robyn AI Agent - OpenAI Integration")
    print("=" * 50)
    
    # Check for OpenAI API key
    if AGENT_CONFIG["openai_api_key"] == "your-openai-api-key-here":
        print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
        print("   The system will use a simple fallback agent instead.")
    else:
        print("✓ OpenAI API key configured")
    
    print()
    
    # Run example usage
    asyncio.run(example_usage())
    
    print("\n🚀 Starting Robyn server...")
    print("Available endpoints:")
    print("  GET  /         - Home page and API info")
    print("  GET  /config   - View current configuration") 
    print("  POST /config   - Update configuration")
    print("  POST /chat     - Chat with AI agent")
    print("  GET  /memory   - View conversation memory")
    print("  DELETE /memory - Clear conversation memory")
    print()
    print("Example requests:")
    print('  curl -X POST http://localhost:8080/chat \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"query": "Hello! How can you help me?", "history": true}\'')
    print()
    print('  curl -X GET http://localhost:8080/memory')
    print()
    
    app.start(port=8080)
