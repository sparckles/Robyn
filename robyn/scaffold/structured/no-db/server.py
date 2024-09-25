from robyn import Robyn
from robyn.helpers import discover_routes
from router import build_routes

# app: Robyn = build_routes()
# OR
app: Robyn = discover_routes()

if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)
