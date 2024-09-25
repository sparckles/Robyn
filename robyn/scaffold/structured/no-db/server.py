from robyn import Robyn
from router import build_routes

app: Robyn = build_routes()

if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)
