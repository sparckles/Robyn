"""
In-process test client for Robyn applications.

Executes route handlers directly without starting a server, making tests
fast and deterministic. Replicates the full request pipeline from server.rs:
before middlewares → handler → global response headers → after middlewares.

Usage::

    from robyn import Robyn
    from robyn.testing import TestClient

    app = Robyn(__file__)

    @app.get("/")
    def index(request):
        return "Hello, Robyn!"

    client = TestClient(app)

    def test_index():
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, Robyn!"
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from robyn.robyn import Headers, MiddlewareType, QueryParams, Request, Response, Url


@dataclass
class TestResponse:
    """Lightweight response wrapper returned by :class:`TestClient` calls."""

    status_code: int
    headers: Headers
    _body: bytes = field(default=b"", repr=False)

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self._body)

    @property
    def content(self) -> bytes:
        return self._body

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


# ---------------------------------------------------------------------------
# Route matching (mirrors matchit::Router from Rust)
# ---------------------------------------------------------------------------

_PARAM_RE = re.compile(r":([^/]+)")
_CATCHALL_RE = re.compile(r"\*([^/]*)")


def _compile_route_pattern(route: str) -> re.Pattern:
    """Compile a Robyn route pattern (``/user/:id``) into a regex."""
    parts: List[str] = []
    for segment in route.strip("/").split("/"):
        if segment.startswith(":"):
            name = segment[1:]
            parts.append(f"(?P<{name}>[^/]+)")
        elif segment.startswith("*"):
            name = segment[1:] or "tail"
            parts.append(f"(?P<{name}>.+)")
        else:
            parts.append(re.escape(segment))

    if parts:
        return re.compile("^/" + "/".join(parts) + "$")
    return re.compile("^/$")


class _RouteTable:
    """Ordered list of (pattern, value) with first-match semantics."""

    def __init__(self) -> None:
        self._entries: List[Tuple[re.Pattern, Any]] = []

    def add(self, path_pattern: str, value: Any) -> None:
        self._entries.append((_compile_route_pattern(path_pattern), value))

    def match(self, path: str) -> Tuple[Optional[Any], Dict[str, str]]:
        for compiled, value in self._entries:
            m = compiled.match(path)
            if m:
                return value, {k: v for k, v in m.groupdict().items() if v is not None}
        return None, {}


# ---------------------------------------------------------------------------
# TestClient
# ---------------------------------------------------------------------------

_HTTP_METHOD_PREFIX_LEN = len("HttpMethod.")


def _method_str(route_type) -> str:
    """``HttpMethod.GET`` → ``"GET"``."""
    return str(route_type)[_HTTP_METHOD_PREFIX_LEN:]


class TestClient:
    """Execute requests against a Robyn app without starting a server.

    The client replicates the pipeline implemented by ``index()`` in
    ``src/server.rs``: global before middlewares → route-specific before
    middleware → handler → global response headers → global after middlewares
    → route-specific after middleware.

    Args:
        app: A :class:`~robyn.Robyn` (or :class:`~robyn.SubRouter`) instance
             with routes already registered.
    """

    def __init__(self, app) -> None:
        self.app = app
        self._loop = asyncio.new_event_loop()

        self._http_routes: Dict[str, _RouteTable] = {}
        self._global_before: list = []
        self._global_after: list = []
        self._mw_before: Dict[str, _RouteTable] = {}
        self._mw_after: Dict[str, _RouteTable] = {}

        self._build()

    # -- setup --------------------------------------------------------------

    def _build(self) -> None:
        for route in self.app.router.get_routes():
            method = _method_str(route.route_type)
            self._http_routes.setdefault(method, _RouteTable()).add(route.route, route.function)

        for mw in self.app.middleware_router.get_global_middlewares():
            if mw.middleware_type == MiddlewareType.BEFORE_REQUEST:
                self._global_before.append(mw.function)
            else:
                self._global_after.append(mw.function)

        for mw in self.app.middleware_router.get_route_middlewares():
            mw_method = _method_str(mw.route_type)
            if mw.middleware_type == MiddlewareType.BEFORE_REQUEST:
                self._mw_before.setdefault(mw_method, _RouteTable()).add(mw.route, mw.function)
            else:
                self._mw_after.setdefault(mw_method, _RouteTable()).add(mw.route, mw.function)

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        if not self._loop.is_closed():
            self._loop.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # -- internals ----------------------------------------------------------

    def _call(self, fn_info, *args):
        """Call a handler (sync or async) and return its result."""
        result = fn_info.handler(*args)
        if asyncio.iscoroutine(result):
            return self._loop.run_until_complete(result)
        return result

    def _build_request(
        self,
        method: str,
        path: str,
        body: Union[str, bytes, None] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        form_data: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, bytes]] = None,
    ) -> Request:
        qp = QueryParams()
        if query_params:
            for k, v in query_params.items():
                qp.set(k, v)

        h = Headers(headers or {})

        body_val: Union[str, bytes] = ""
        if body is not None:
            body_val = body if isinstance(body, bytes) else body.encode("utf-8")

        return Request(
            qp,
            h,
            {},
            body_val,
            method,
            Url("http", "testclient", path),
            form_data or {},
            files or {},
            None,
            "127.0.0.1",
        )

    def _execute(self, method: str, path: str, **kwargs) -> TestResponse:
        request = self._build_request(method, path, **kwargs)

        # ---- before middlewares (global) ----------------------------------
        for mw_fn in self._global_before:
            result = self._call(mw_fn, request)
            if result is not None:
                if isinstance(result, Response):
                    return self._to_test_response(result)
                request = result

        # ---- before middleware (route-specific) ---------------------------
        mw_table = self._mw_before.get(method)
        if mw_table is not None:
            mw_fn, mw_params = mw_table.match(path)
            if mw_fn is not None:
                request.path_params = mw_params
                result = self._call(mw_fn, request)
                if result is not None:
                    if isinstance(result, Response):
                        return self._to_test_response(result)
                    request = result

        # ---- route match --------------------------------------------------
        route_table = self._http_routes.get(method)
        if route_table is None:
            return TestResponse(status_code=404, headers=Headers({}), _body=b"Not Found")

        fn_info, path_params = route_table.match(path)
        if fn_info is None:
            return TestResponse(status_code=404, headers=Headers({}), _body=b"Not Found")

        request.path_params = path_params

        # ---- execute handler ----------------------------------------------
        response = self._call(fn_info, request)

        if not isinstance(response, Response):
            if isinstance(response, (dict, list)):
                body = json.dumps(response).encode("utf-8")
            elif isinstance(response, bytes):
                body = response
            else:
                body = str(response).encode("utf-8")
            return TestResponse(
                status_code=200,
                headers=Headers({}),
                _body=body,
            )

        # ---- merge global response headers --------------------------------
        excluded = self.app.excluded_response_headers_paths or []
        if path not in excluded and not self.app.response_headers.is_empty():
            if isinstance(response.headers, dict):
                response.headers = Headers(response.headers)
            resp_headers = response.headers
            global_dict = self.app.response_headers.get_headers()
            for key, values in global_dict.items():
                for val in values:
                    resp_headers.append(key, val)

        # ---- after middlewares (global) -----------------------------------
        for mw_fn in self._global_after:
            response = self._call_after_mw(mw_fn, request, response)

        # ---- after middleware (route-specific) ----------------------------
        mw_table = self._mw_after.get(method)
        if mw_table is not None:
            mw_fn, _ = mw_table.match(path)
            if mw_fn is not None:
                response = self._call_after_mw(mw_fn, request, response)

        return self._to_test_response(response)

    def _call_after_mw(self, fn_info, request, response):
        if fn_info.number_of_params <= 1:
            result = self._call(fn_info, response)
        else:
            result = self._call(fn_info, request, response)
        if isinstance(result, Response):
            return result
        return response

    @staticmethod
    def _to_test_response(response: Response) -> TestResponse:
        body = response.description
        if isinstance(body, str):
            body = body.encode("utf-8")
        elif isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif not isinstance(body, bytes):
            body = str(body).encode("utf-8")

        return TestResponse(
            status_code=response.status_code,
            headers=response.headers,
            _body=body,
        )

    # -- public HTTP methods ------------------------------------------------

    def get(self, path: str, **kw) -> TestResponse:
        return self._execute("GET", path, **kw)

    def post(self, path: str, json_data: Any = None, **kw) -> TestResponse:
        if json_data is not None and "body" not in kw:
            kw["body"] = json.dumps(json_data)
            kw.setdefault("headers", {})["Content-Type"] = "application/json"
        return self._execute("POST", path, **kw)

    def put(self, path: str, json_data: Any = None, **kw) -> TestResponse:
        if json_data is not None and "body" not in kw:
            kw["body"] = json.dumps(json_data)
            kw.setdefault("headers", {})["Content-Type"] = "application/json"
        return self._execute("PUT", path, **kw)

    def patch(self, path: str, json_data: Any = None, **kw) -> TestResponse:
        if json_data is not None and "body" not in kw:
            kw["body"] = json.dumps(json_data)
            kw.setdefault("headers", {})["Content-Type"] = "application/json"
        return self._execute("PATCH", path, **kw)

    def delete(self, path: str, json_data: Any = None, **kw) -> TestResponse:
        if json_data is not None and "body" not in kw:
            kw["body"] = json.dumps(json_data)
            kw.setdefault("headers", {})["Content-Type"] = "application/json"
        return self._execute("DELETE", path, **kw)

    def head(self, path: str, **kw) -> TestResponse:
        return self._execute("HEAD", path, **kw)

    def options(self, path: str, **kw) -> TestResponse:
        return self._execute("OPTIONS", path, **kw)
