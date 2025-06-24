#!/usr/bin/env python3
"""Simple Robyn AI Agents Example"""

import os

from robyn import Robyn
from robyn.ai import agent, configure, memory

app = Robyn(__file__)
ai_agent = None


@app.startup_handler
async def startup():
    global ai_agent

    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to use AI features")
        return

    user_memory = memory(provider="inmemory", user_id="user")
    config = configure(openai_api_key=os.getenv("OPENAI_API_KEY"))
    ai_agent = agent(memory=user_memory, config=config)


@app.post("/chat")
async def chat(request):
    if not ai_agent:
        return {"error": "AI not available"}

    query = request.json().get("query")
    if not query:
        return {"error": "Query required"}

    result = await ai_agent.run(query)
    return {"response": result.get("response")}


@app.get("/")
def home():
    return {"message": "Robyn AI Agent", "endpoint": "/chat"}


if __name__ == "__main__":
    app.start(port=8080)
