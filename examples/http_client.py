"""Call another HTTP API from a Robyn handler.

Robyn serves incoming requests. It does not bundle an outbound HTTP client —
use httpx, aiohttp, rusty-req, or any other async client from an `async`
route. This file uses rusty-req (`pip install rusty-req`).

Run:

    python examples/http_client.py

Then:

    curl http://127.0.0.1:8080/todo/1
    curl -X POST http://127.0.0.1:8080/posts \\
         -H 'Content-Type: application/json' \\
         -d '{"title": "robyn", "body": "hello", "userId": 1}'
    curl http://127.0.0.1:8080/fan-out
"""

import json
from typing import Any

try:
    import rusty_req
    from rusty_req import ConcurrencyMode, RequestItem
except ImportError as exc:
    raise SystemExit("This example requires rusty-req. Install it with: pip install rusty-req") from exc

from robyn import Request, Robyn

app = Robyn(__file__)

UPSTREAM = "https://jsonplaceholder.typicode.com"


def _as_dict(value: Any) -> dict[str, Any]:
    """rusty-req may return nested JSON as a string or as an object."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def parse_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a rusty-req result into status / body / exception."""
    status = raw.get("http_status", 0)
    if isinstance(status, str):
        status = int(status) if status.isdigit() else 0

    response = _as_dict(raw.get("response"))
    meta = _as_dict(raw.get("meta"))
    exception = _as_dict(raw.get("exception"))
    if not exception.get("type"):
        exception = None

    text = response.get("content") or ""
    try:
        body: Any = json.loads(text) if text else None
    except json.JSONDecodeError:
        body = text

    return {
        "status": status,
        "ok": exception is None and 200 <= status < 400,
        "body": body,
        "text": text,
        "headers": response.get("headers") or {},
        "tag": meta.get("tag"),
        "elapsed": meta.get("process_time"),
        "exception": exception,
    }


@app.get("/")
def index():
    return {
        "message": "Outbound HTTP from a Robyn handler",
        "endpoints": {
            "GET /todo/:id": "Single GET",
            "POST /posts": "Forward the JSON body upstream",
            "GET /fan-out": "Several requests in parallel",
            "GET /fetch?url=": "GET an arbitrary URL",
        },
    }


@app.get("/todo/:id")
async def get_todo(request: Request):
    todo_id = request.path_params["id"]
    raw = await rusty_req.fetch_single(
        url=f"{UPSTREAM}/todos/{todo_id}",
        method="GET",
    )
    result = parse_result(raw)
    if not result["ok"]:
        return {"error": result["exception"] or result["text"], "status": result["status"]}, 502
    return {"todo": result["body"], "elapsed": result["elapsed"]}


@app.post("/posts")
async def create_post(request: Request):
    # rusty-req uses `params` as the JSON body for POST/PUT/PATCH.
    raw = await rusty_req.fetch_single(
        url=f"{UPSTREAM}/posts",
        method="POST",
        params=request.json(),
        headers={"Accept": "application/json"},
    )
    result = parse_result(raw)
    return {"status": result["status"], "upstream": result["body"]}


@app.get("/fan-out")
async def fan_out():
    # fetch_requests runs the batch concurrently. SELECT_ALL returns
    # results as they finish; JOIN_ALL waits for the whole batch.
    raw_results = await rusty_req.fetch_requests(
        [
            RequestItem(url=f"{UPSTREAM}/todos/1", method="GET", tag="todo-1", timeout=5.0),
            RequestItem(url=f"{UPSTREAM}/todos/2", method="GET", tag="todo-2", timeout=5.0),
            RequestItem(url=f"{UPSTREAM}/users/1", method="GET", tag="user-1", timeout=5.0),
        ],
        total_timeout=8.0,
        mode=ConcurrencyMode.SELECT_ALL,
    )
    results = [parse_result(item) for item in raw_results]
    return {
        "count": len(results),
        "results": [
            {
                "tag": item["tag"],
                "status": item["status"],
                "ok": item["ok"],
                "body": item["body"] if item["ok"] else item["exception"],
            }
            for item in results
        ],
    }


@app.get("/fetch")
async def fetch_url(request: Request):
    url = request.query_params.get("url")
    if not url:
        return {"error": "query parameter 'url' is required"}, 400
    raw = await rusty_req.fetch_single(url=url, method="GET")
    result = parse_result(raw)
    return {
        "url": url,
        "status": result["status"],
        "ok": result["ok"],
        "body": result["body"],
        "exception": result["exception"],
    }


if __name__ == "__main__":
    app.start(port=8080)
