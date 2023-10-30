from robyn import Robyn
from .models import User


app = Robyn(__file__)


@app.get("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    # create a configured "Session" class
    app.start(host="0.0.0.0", port=8080)
