"""Unit tests for authentication-handler propagation to SubRouters (#1026).

A SubRouter without its own handler should inherit one from the router that
includes it, including through nested SubRouters and regardless of whether
configure_authentication() is called before or after include_router().
"""

from robyn import Robyn, SubRouter
from robyn.authentication import AuthenticationHandler, BearerGetter, Identity


class _Handler(AuthenticationHandler):
    def authenticate(self, request):
        return Identity(claims={"k": "v"})


def _mw(router):
    return router.middleware_router.authentication_handler


def test_configure_then_include_propagates():
    app = Robyn(__file__)
    handler = _Handler(token_getter=BearerGetter())
    app.configure_authentication(handler)

    sub = SubRouter(prefix="/sub")
    app.include_router(sub)

    assert sub.authentication_handler is handler
    assert _mw(sub) is handler


def test_include_then_configure_propagates():
    app = Robyn(__file__)
    sub = SubRouter(prefix="/sub")
    app.include_router(sub)

    handler = _Handler(token_getter=BearerGetter())
    app.configure_authentication(handler)

    assert sub.authentication_handler is handler
    assert _mw(sub) is handler


def test_nested_subrouters_inherit():
    app = Robyn(__file__)
    parent = SubRouter(prefix="/parent")
    child = SubRouter(prefix="/child")
    parent.include_router(child)
    app.include_router(parent)

    handler = _Handler(token_getter=BearerGetter())
    app.configure_authentication(handler)

    # both levels inherit the app handler
    assert parent.authentication_handler is handler
    assert child.authentication_handler is handler


def test_subrouter_keeps_its_own_handler():
    app = Robyn(__file__)
    own = _Handler(token_getter=BearerGetter())
    sub = SubRouter(prefix="/sub")
    sub.configure_authentication(own)

    app_handler = _Handler(token_getter=BearerGetter())
    app.configure_authentication(app_handler)
    app.include_router(sub)

    # the SubRouter's own handler must not be overridden by the app's
    assert sub.authentication_handler is own


def test_subrouter_own_handler_passes_down_to_descendant():
    app = Robyn(__file__)
    parent = SubRouter(prefix="/parent")
    parent_handler = _Handler(token_getter=BearerGetter())
    parent.configure_authentication(parent_handler)

    child = SubRouter(prefix="/child")
    parent.include_router(child)
    app.include_router(parent)

    # child had no handler -> inherits the parent SubRouter's, not the app's (app has none)
    assert child.authentication_handler is parent_handler
