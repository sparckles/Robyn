

# robyn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../robyn")
# sys.path.insert(0, robyn_path)

from robyn import Robyn, static_file, jsonify, SocketHeld
import asyncio
import os
import pathlib

app = Robyn(__file__)


callCount = 0


@app.get("/")
async def hello(request):
    global callCount
    callCount += 1
    message = "Called " + str(callCount) + " times"
    return jsonify(request)


@app.get("/test/:id")
async def test(request):
    print(request)
    current_file_path = pathlib.Path(__file__).parent.resolve()
    html_file = os.path.join(current_file_path, "index.html")

    return static_file(html_file)

@app.get("/jsonify")
async def json_get():
    return jsonify({"hello": "world"})


@app.post("/jsonify/:id")
async def json(request):
    print(request["params"]["id"])
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
    current_file_path = pathlib.Path(__file__).parent.resolve()
    os.path.join(current_file_path, "build")
    app.add_directory(route="/test_dir",directory_path=os.path.join(current_file_path, "build/"), index_file="index.html")
    app.start(port=5000, url='0.0.0.0')
