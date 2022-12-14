from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def index():
    return {
        "status_code": 200,
        "body": "Hello World!",
        "headers": {
            "Content-Type": "text/plain"
        }
    }


app.start(url="127.0.0.1", port=8000)
