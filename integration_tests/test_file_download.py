import pytest

from integration_tests.helpers.http_methods_helpers import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["sync", "async"])
@pytest.mark.parametrize(
    "file_name, content_type",
    [("", "text/plain"), ("test.txt", "text/plain"), ("test.unknownext", "application/octet-stream"), ("test", "application/octet-stream")],
)
def test_file_download(function_type: str, file_name: str, content_type: str, session):
    r = get(f"/{function_type}/file/download?file_name={file_name}")
    assert r.headers.get("Content-Disposition") == f"attachment; filename={file_name or 'test.txt'}"
    assert r.headers.get("Content-Type") == content_type

    assert r.text == "This is a test file for the downloading purpose"
