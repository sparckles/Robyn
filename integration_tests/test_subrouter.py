import pytest
import requests

from helpers.http_methods_helpers import generic_http_helper, head


@pytest.mark.parametrize(
    "http_method_type",
    ["get", "post", "put", "delete", "patch", "options", "trace"],
)
def test_sub_router(http_method_type, session):
    response = generic_http_helper(http_method_type, "sub_router/foo")
    assert response.json() == {"message": "foo"}


def test_sub_router_head(session):
    response = head("sub_router/foo")
    assert response.text == ""  # response body is expected to be empty
