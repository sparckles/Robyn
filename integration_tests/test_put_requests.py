import pytest
from http_methods_helpers import put

@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_put_with_param(function_type: str, session):
    res = put(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
