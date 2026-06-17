"""Unit tests for SubRouter prefix handling.

Covers nested SubRouter prefix accumulation for HTTP routes (#865, #1394),
prefixing of routes registered via add_route (#1256), the modern prefix-first
syntax with router-level tags and the optional/deprecated module argument
(#554), and that auth middleware paths stay in sync with their routes.
These inspect the in-memory route tables directly, so no server is started.
"""

import warnings

import pytest

from robyn import Robyn, SubRouter


def _http_paths(app: Robyn) -> set[str]:
    return {route.route for route in app.router.routes}


def _tags_for(app: Robyn, path: str) -> list[str]:
    return next(route.openapi_tags for route in app.router.routes if route.route == path)


def _middleware_paths(app: Robyn) -> set[str]:
    return {mw.route for mw in app.middleware_router.route_middlewares}


def test_single_level_subrouter_prefix():
    app = Robyn(__file__)
    sub = SubRouter(prefix="/sub")

    @sub.get("/foo")
    def foo():
        return "foo"

    app.include_router(sub)

    assert "/sub/foo" in _http_paths(app)


def test_nested_subrouter_http_prefix_accumulates():
    """#865 / #1394: nested SubRouter HTTP routes must accumulate parent prefixes."""
    app = Robyn(__file__)
    v1 = SubRouter(prefix="/v1")
    hello = SubRouter(prefix="/hello")

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
    a = SubRouter(prefix="/a")
    b = SubRouter(prefix="/b")
    c = SubRouter(prefix="/c")

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
    sub = SubRouter(prefix="/sub")

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
    v1 = SubRouter(prefix="/v1")
    secure = SubRouter(prefix="/secure")

    @secure.get("/data", auth_required=True)
    def data():
        return "secret"

    v1.include_router(secure)
    app.include_router(v1)

    assert "/v1/secure/data" in _http_paths(app)
    # the before-request auth middleware must be registered at the same final path
    assert "/v1/secure/data" in _middleware_paths(app)


def test_positional_prefix():
    """#554: prefix may be passed positionally, e.g. SubRouter("/users")."""
    app = Robyn(__file__)
    sub = SubRouter("/users")

    @sub.get("/")
    def list_users():
        return "users"

    app.include_router(sub)
    assert "/users" in _http_paths(app)


def test_router_level_tags_applied_to_routes():
    """#554 modern syntax: SubRouter(tags=...) tags every contributed route."""
    app = Robyn(__file__)
    sub = SubRouter(prefix="/users", tags=["users"])

    @sub.get("/profile")
    def profile():
        return "profile"

    app.include_router(sub)
    assert "users" in _tags_for(app, "/users/profile")


def test_router_level_tags_accumulate_through_nesting():
    app = Robyn(__file__)
    v1 = SubRouter(prefix="/v1", tags=["v1"])
    users = SubRouter(prefix="/users", tags=["users"])

    @users.get("/me")
    def me():
        return "me"

    v1.include_router(users)
    app.include_router(v1)

    tags = _tags_for(app, "/v1/users/me")
    assert "v1" in tags
    assert "users" in tags


def test_legacy_module_argument_still_works_but_warns():
    """Back-compat: SubRouter(__name__, prefix=...) keeps working, with a warning."""
    app = Robyn(__file__)

    with pytest.warns(DeprecationWarning):
        sub = SubRouter(__name__, prefix="/legacy")

    @sub.get("/foo")
    def foo():
        return "foo"

    app.include_router(sub)
    assert "/legacy/foo" in _http_paths(app)


def test_legacy_positional_module_and_prefix_still_works():
    """Back-compat: SubRouter(__file__, "/x") fully-positional form keeps working."""
    app = Robyn(__file__)

    with pytest.warns(DeprecationWarning):
        sub = SubRouter(__file__, "/legacy2")

    @sub.get("/foo")
    def foo():
        return "foo"

    app.include_router(sub)
    assert "/legacy2/foo" in _http_paths(app)


def test_modern_syntax_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        SubRouter(prefix="/clean")
        SubRouter("/clean2")
