from robyn import Robyn, static_file, jsonify, WS
import asyncio
import os
import pathlib

app = Robyn(__file__)
websocket = WS(app, "/web_socket")
i = -1

@websocket.on("message")
async def connect():
    global i
    i+=1
    if i==0:
        return "Whaaat??"
    elif i==1:
        return "Whooo??"
    elif i==2:
        i = -1
        return "*chika* *chika* Slim Shady."

@websocket.on("close")
def close():
    return "GoodBye world, from ws"

@websocket.on("connect")
def message():
    return "Hello world, from ws"


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
async def post():
    return "POST Request"

@app.post("/post_with_body")
async def postreq_with_body(request):
    return bytearray(request["body"]).decode("utf-8")

@app.put("/put")
async def put(request):
    return "PUT Request"

@app.put("/put_with_body")
async def putreq_with_body(request):
    print(request)
    return bytearray(request["body"]).decode("utf-8")


@app.delete("/delete")
async def delete():
    return "DELETE Request"

@app.delete("/delete_with_body")
async def deletereq_with_body(request):
    return bytearray(request["body"]).decode("utf-8")


@app.patch("/patch")
async def patch():
    return "PATCH Request"

@app.patch("/patch_with_body")
async def patchreq_with_body(request):
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
    ROBYN_URL = os.getenv("ROBYN_URL", '0.0.0.0')
    app.add_header("server", "robyn")
    current_file_path = pathlib.Path(__file__).parent.resolve()
    os.path.join(current_file_path, "build")
    app.add_directory(route="/test_dir",directory_path=os.path.join(current_file_path, "build/"), index_file="index.html")
    app.start(port=5000, url=ROBYN_URL)
