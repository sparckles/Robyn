import pytest
from http_methods_helpers import patch


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_patch_with_param(function_type: str, session):
    res = patch(f"/{function_type}/body", data={"hello": "world"})
    assert res.text == "hello=world"
