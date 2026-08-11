"""Minimal app used by test_graceful_shutdown.py.

Verifies that SIGTERM triggers a graceful shutdown (clean exit + shutdown handler)
instead of hanging until SIGKILL. See issue #1324.
"""

import sys

from robyn import Robyn

app = Robyn(__file__)

_sentinel_path = sys.argv[1]
_port = int(sys.argv[2])


@app.get("/")
def index(request):
    return "ok"


def _on_shutdown():
    with open(_sentinel_path, "w") as handle:
        handle.write("shutdown")


app.shutdown_handler(_on_shutdown)


if __name__ == "__main__":
    app.start(host="127.0.0.1", port=_port, _check_port=False)
