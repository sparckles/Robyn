from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def h():
    return "Hello, world!"


app.start()
