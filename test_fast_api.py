from fastapi import FastAPI
import asyncio

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/sleeper")
async def sleeper():
    await asyncio.sleep(5)
    return {"message": "Hello World"}

