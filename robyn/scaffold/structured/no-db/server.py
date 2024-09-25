from robyn import Robyn
from robyn.helpers import discover_routes

app: Robyn = discover_routes("api.handlers")

if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)
