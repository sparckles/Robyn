"""Call another HTTP API from a Robyn handler.

Robyn serves incoming requests. It does not bundle an outbound HTTP client, so
use any async client from an ``async`` handler. This example uses httpx
(``pip install httpx``); aiohttp or another async client drops in the same way.

Run:

    python examples/http_client.py

Then:

    curl http://127.0.0.1:8080/todo/1
    curl -X POST http://127.0.0.1:8080/posts \\
         -H 'Content-Type: application/json' \\
         -d '{"title": "robyn", "body": "hello", "userId": 1}'
    curl http://127.0.0.1:8080/fan-out
"""

import asyncio
import json
from typing import Any

try:
    import httpx
except ImportError as exc:
    raise SystemExit("This example requires httpx. Install it with: pip install httpx") from exc

from robyn import Headers, Request, Response, Robyn

app = Robyn(__file__)

UPSTREAM = "https://jsonplaceholder.typicode.com"
TIMEOUT = httpx.Timeout(5.0)


def json_response(body: dict[str, Any], status_code: int) -> Response:
    """Build a JSON response with an explicit status code."""
    return Response(
        status_code=status_code,
        headers=Headers({"Content-Type": "application/json"}),
        description=json.dumps(body),
    )


def upstream_error(error: httpx.HTTPError | httpx.Response) -> Response:
    """Map an upstream failure onto a 502 for our own caller."""
    if isinstance(error, httpx.Response):
        detail: dict[str, Any] = {"status": error.status_code, "body": error.text}
    else:
        detail = {"error": f"{type(error).__name__}: {error}"}
    return json_response({"error": "upstream request failed", "upstream": detail}, 502)


@app.get("/")
def index():
    """List the sample routes."""
    return {
        "message": "Outbound HTTP from a Robyn handler",
        "endpoints": {
            "GET /todo/:id": "Single GET",
            "POST /posts": "Forward the JSON body upstream",
            "GET /fan-out": "Several requests in parallel",
        },
    }


@app.get("/todo/:id")
async def get_todo(request: Request):
    """Fetch one todo from the upstream API."""
    todo_id = request.path_params["id"]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{UPSTREAM}/todos/{todo_id}")
    except httpx.HTTPError as exc:
        return upstream_error(exc)
    if response.is_error:
        return upstream_error(response)
    return {"todo": response.json(), "elapsed": response.elapsed.total_seconds()}


@app.post("/posts")
async def create_post(request: Request):
    """Forward the incoming JSON body to the upstream API."""
    payload = request.json()
    if not isinstance(payload, dict):
        return json_response({"error": "JSON body must be an object"}, 400)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{UPSTREAM}/posts", json=payload)
    except httpx.HTTPError as exc:
        return upstream_error(exc)
    if response.is_error:
        return upstream_error(response)
    return {"status": response.status_code, "upstream": response.json()}


@app.get("/fan-out")
async def fan_out():
    """Send several upstream GETs concurrently and report each outcome."""
    paths = ["/todos/1", "/todos/2", "/users/1"]
    async with httpx.AsyncClient(base_url=UPSTREAM, timeout=TIMEOUT) as client:
        outcomes = await asyncio.gather(*(client.get(path) for path in paths), return_exceptions=True)

    results = []
    for path, outcome in zip(paths, outcomes):
        if isinstance(outcome, BaseException):
            results.append({"path": path, "ok": False, "error": f"{type(outcome).__name__}: {outcome}"})
        else:
            results.append(
                {"path": path, "ok": outcome.is_success, "status": outcome.status_code, "body": outcome.json() if outcome.is_success else outcome.text}
            )
    return {"count": len(results), "results": results}


if __name__ == "__main__":
    app.start(port=8080)
