import pytest

from robyn import Request, Robyn
from robyn.testing import TestClient


@pytest.fixture
def client():
    app = Robyn(__file__)

    @app.get("/items/:id")
    def item(request: Request):
        return request.path_params["id"]

    @app.get("/files/*path")
    def files(request: Request):
        return request.path_params["path"]

    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "encoded, expected",
    [
        ("attempt%3A1", "attempt:1"),
        ("a%20b", "a b"),
        ("a+b", "a+b"),
        ("a%2Fb", "a/b"),
        ("%252F", "%2F"),
        ("%E6%9D%B1%E4%BA%AC", "東京"),
    ],
)
def test_test_client_decodes_path_params_like_the_server(client, encoded, expected):
    assert client.get(f"/items/{encoded}").text == expected


def test_test_client_decodes_catch_all_params(client):
    assert client.get("/files/a%2Fb/c%20d+e/%252F").text == "a/b/c d+e/%2F"
