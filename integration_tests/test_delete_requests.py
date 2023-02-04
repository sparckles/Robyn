import pytest
from http_methods_helpers import delete


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_delete(function_type: str, session):
    res = delete(f"/{function_type}/dict")
    assert res.text == f"{function_type} dict delete"
    assert function_type in res.headers
    assert res.headers[function_type] == "dict"


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_delete_with_param(function_type: str, session):
    res = delete(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
