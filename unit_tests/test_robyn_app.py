from robyn.router import Router
from robyn import Robyn, SubRouter


def test_app_creation():
    app = Robyn(__file__)
    router = app.router
    assert isinstance(router, Router)
    assert len(router.routes) == 0


def test_subrouter_creation():
    sub = SubRouter(__name__, prefix="/frontend")
    router = sub.router
    assert isinstance(router, Router)
    assert len(router.routes) == 0
