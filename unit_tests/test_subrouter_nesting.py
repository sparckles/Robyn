"""Unit tests for SubRouter prefix handling.

Covers nested SubRouter prefix accumulation for HTTP routes (#865, #1394),
prefixing of routes registered via add_route (#1256), the optional file_object
argument (#554) and that auth middleware paths stay in sync with their routes.
These inspect the in-memory route tables directly, so no server is started.
"""

from robyn import Robyn, SubRouter


def _http_paths(app: Robyn) -> set[str]:
    return {route.route for route in app.router.routes}


def _middleware_paths(app: Robyn) -> set[str]:
    return {mw.route for mw in app.middleware_router.route_middlewares}


def test_single_level_subrouter_prefix():
    app = Robyn(__file__)
    sub = SubRouter(__name__, prefix="/sub")

    @sub.get("/foo")
    def foo():
        return "foo"

    app.include_router(sub)

    assert "/sub/foo" in _http_paths(app)


def test_nested_subrouter_http_prefix_accumulates():
    """#865 / #1394: nested SubRouter HTTP routes must accumulate parent prefixes."""
    app = Robyn(__file__)
    v1 = SubRouter(__name__, prefix="/v1")
    hello = SubRouter(__name__, prefix="/hello")

    @hello.get("/index")
    def index():
        return "hi"

    v1.include_router(hello)
    app.include_router(v1)

    paths = _http_paths(app)
    assert "/v1/hello/index" in paths
    assert "/hello/index" not in paths


def test_deeply_nested_subrouter_prefix_accumulates():
    app = Robyn(__file__)
    a = SubRouter(__name__, prefix="/a")
    b = SubRouter(__name__, prefix="/b")
    c = SubRouter(__name__, prefix="/c")

    @c.get("/leaf")
    def leaf():
        return "leaf"

    b.include_router(c)
    a.include_router(b)
    app.include_router(a)

    assert "/a/b/c/leaf" in _http_paths(app)


def test_subrouter_add_route_applies_prefix():
    """#1256: add_route() on a SubRouter must apply the prefix like the decorators."""
    app = Robyn(__file__)
    sub = SubRouter(__name__, prefix="/sub")

    def login():
        return "ok"

    sub.add_route("GET", "/login", login)
    app.include_router(sub)

    assert "/sub/login" in _http_paths(app)


def test_subrouter_file_object_is_optional():
    """#554: SubRouter should not require __name__/__file__ to be passed."""
    sub = SubRouter(prefix="/no-name")

    @sub.get("/foo")
    def foo():
        return "foo"

    app = Robyn(__file__)
    app.include_router(sub)
    assert "/no-name/foo" in _http_paths(app)


def test_nested_auth_middleware_path_matches_route():
    """Auth middleware path must accumulate prefixes in lockstep with the route."""
    app = Robyn(__file__)
    v1 = SubRouter(__name__, prefix="/v1")
    secure = SubRouter(__name__, prefix="/secure")

    @secure.get("/data", auth_required=True)
    def data():
        return "secret"

    v1.include_router(secure)
    app.include_router(v1)

    assert "/v1/secure/data" in _http_paths(app)
    # the before-request auth middleware must be registered at the same final path
    assert "/v1/secure/data" in _middleware_paths(app)
