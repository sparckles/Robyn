import pytest
from http_methods_helpers import post


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_post_with_param(function_type: str, session):
    res = post(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
