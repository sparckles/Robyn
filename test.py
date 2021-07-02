from robyn import Robyn, static_file
import asyncio

app = Robyn()

callCount = 0

@app.get("/")
async def h():
    global callCount
    callCount +=  1
    message = "Called " + str(callCount) + " times"
    return message

@app.get("/test")
async def test():
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "index.html"))
    return static_file(path)


@app.get("/sleep")
async def sleeper():
    await asyncio.sleep(5)
    return "sleep function"

@app.get("/blocker")
def blocker():
    import time
    time.sleep(10)
    return "blocker function"

if __name__=="__main__":
    app.start(port=5000)

