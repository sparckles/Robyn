"""
Standalone Robyn app with ALLOW_CORS enabled, used by CORS integration tests.
Runs on a separate port (8083) so it doesn't conflict with base_routes.py.
"""

import os

from robyn import ALLOW_CORS, Robyn

app = Robyn(__file__)

ALLOWED_ORIGINS = ["http://localhost:3000", "https://frontend.example.com"]
ALLOW_CORS(app, origins=ALLOWED_ORIGINS)


@app.get("/")
def index():
    return "OK"


@app.post("/data")
def post_data(request):
    return "created"


@app.get("/custom-header")
def custom_header(request):
    from robyn import Response

    return Response(
        status_code=200,
        headers={"x-custom": "hello"},
        description="custom",
    )


if __name__ == "__main__":
    port = int(os.getenv("ROBYN_PORT", "8083"))
    app.start(port=port, _check_port=False)
