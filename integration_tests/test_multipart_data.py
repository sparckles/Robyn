import pytest
from integration_tests.helpers.http_methods_helpers import multipart_post


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync"])
def test_form_data(function_type: str, session):
    res = multipart_post(f"/{function_type}/form_data", files={"hello": "world"})
    assert "multipart" in res.text


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync"])
def test_multipart_file(function_type: str, session):
    res = multipart_post(f"/{function_type}/multipart-file", files={"hello": "world"})
    assert "hello" in res.text
