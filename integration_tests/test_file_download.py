from utils import get


def test_file_download_sync(session):
    r = get("/sync/file/download")
    assert r.headers["Content-Disposition"] == "attachment"
    assert r.text == "This is a test file for the downloading purpose\n"


def test_file_download_async(session):
    r = get("/async/file/download")
    assert r.headers["Content-Disposition"] == "attachment"
    assert r.text == "This is a test file for the downloading purpose\n"
