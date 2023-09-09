import pytest
from integration_tests.helpers.http_methods_helpers import patch


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_patch(function_type: str, session):
    res = patch(f"/{function_type}/dict")
    assert res.text == f"{function_type} dict patch"
    assert function_type in res.headers
    assert res.headers[function_type] == "dict"


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_patch_with_param(function_type: str, session):
    res = patch(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
