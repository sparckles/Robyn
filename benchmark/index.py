from robyn import Robyn, static_file, jsonify, WS
import os

app = Robyn(__file__)
websocket = WS(app, "/web_socket")
i = -1


@app.get("/bruhh", const=True)
async def bruhh(request):
    return "Hello world bruhh"


@app.get("/slow")
async def slow(request):
    return "Hello world"

if __name__ == "__main__":
    ROBYN_URL = os.getenv("ROBYN_URL", "0.0.0.0")
    app.start(port=5000, url=ROBYN_URL)



