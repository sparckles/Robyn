import pytest
import requests


@pytest.mark.parametrize(
    "http_method_type",
    ["get", "post", "put", "delete", "patch", "options", "trace"],
)
def test_sub_router(http_method_type, session):
    response = requests.request(http_method_type, "http://127.0.0.1:8080/sub_router/foo")
    assert response.status_code == 200
    assert response.json() == {"message": "foo"}


# head request
def test_sub_router_head(session):
    response = requests.head("http://127.0.0.1:8080/sub_router/foo")
    assert response.status_code == 200
    assert response.text == ""  # response body is expected to be empty
