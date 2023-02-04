import pytest
from http_methods_helpers import get


@pytest.mark.parametrize("function_type", ["sync", "async"])
def test_file_download(function_type: str, session):
    r = get(f"/{function_type}/file/download")
    assert r.headers["Content-Disposition"] == "attachment"
    assert r.text == "This is a test file for the downloading purpose\n"
