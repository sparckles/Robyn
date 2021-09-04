import sys
import os

robyn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../robyn")
sys.path.insert(0, robyn_path)

from robyn import Robyn, static_file, jsonify
import asyncio

app = Robyn(__file__)

callCount = 0


@app.get("/")
async def h(request):
    print(request)
    global callCount
    callCount += 1
    message = "Called " + str(callCount) + " times"
    return message

@app.get("/test")
async def test():
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "index.html"))
    return static_file(path)

@app.post("/jsonify")
async def json(request):
    print(request)
    return jsonify({"hello": "world"})

@app.post("/post")
async def postreq(request):
    return bytearray(request["body"]).decode("utf-8")

@app.put("/put")
async def putreq(request):
    return bytearray(request["body"]).decode("utf-8")

@app.delete("/delete")
async def deletereq(request):
    return bytearray(request["body"]).decode("utf-8")

@app.patch("/patch")
async def patchreq(request):
    return bytearray(request["body"]).decode("utf-8")

@app.get("/sleep")
async def sleeper():
    await asyncio.sleep(5)
    return "sleep function"


@app.get("/blocker")
def blocker():
    import time
    time.sleep(10)
    return "blocker function"


if __name__ == "__main__":
    app.add_header("server", "robyn")
    app.add_directory(route="/test_dir",directory_path="./test_dir/build", index_file="index.html")
    app.start(port=5000)
