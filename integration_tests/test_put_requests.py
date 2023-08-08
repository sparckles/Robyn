import pytest
from integration_tests.helpers.http_methods_helpers import put


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_put(function_type: str, session):
    res = put(f"/{function_type}/dict")
    assert res.text == f"{function_type} dict put"
    assert function_type in res.headers
    assert res.headers[function_type] == "dict"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_put_with_param(function_type: str, session):
    res = put(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
