import pytest
from http_methods_helpers import post


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_post(function_type: str, session):
    res = post(f"/{function_type}/dict")
    assert res.text == f"{function_type} dict post"
    assert function_type in res.headers
    assert res.headers[function_type] == "dict"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_post_with_param(function_type: str, session):
    res = post(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
