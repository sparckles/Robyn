import pytest

from integration_tests.helpers.http_methods_helpers import multipart_post

# Binary payload with bytes that are not valid UTF-8, to prove the upload is
# saved verbatim rather than being mangled by text decoding (#495).
UPLOAD_CONTENT = b"robyn binary upload \x00\x01\x02\xff\xfe contents"


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


def test_multipart_file_save(session):
    # Upload a file, have the server persist it, then read the saved bytes back
    # and assert they round-trip exactly (#495).
    res = multipart_post("/sync/multipart-file/save", files={"report.bin": UPLOAD_CONTENT})

    saved = res.json()
    assert "report.bin" in saved
    assert saved["report.bin"]["size"] == len(UPLOAD_CONTENT)

    with open(saved["report.bin"]["path"], "rb") as saved_file:
        assert saved_file.read() == UPLOAD_CONTENT
