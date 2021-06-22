from robyn import Robyn
import asyncio

app = Robyn()

@app.get("/")
async def h():
    print("This is the message from coroutine")
    return "not sleep function"

@app.get("/sleep")
async def sleeper():
    await asyncio.sleep(5)
    return "sleep function"

@app.get("/blocker")
def blocker():
    import time
    time.sleep(10)
    return "blocker function"

app.start()

