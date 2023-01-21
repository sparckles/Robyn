import requests

BASE_URL = "http://127.0.0.1:8080"


def test_file_download_sync(session):
    r = requests.get(f"{BASE_URL}/file_download_sync")
    assert r.status_code == 200
    assert r.headers["Content-Disposition"] == "attachment"
    assert r.text == "This is a test file for the downloading purpose\n"


def test_file_download_async(session):
    r = requests.get(f"{BASE_URL}/file_download_async")
    assert r.status_code == 200
    assert r.headers["Content-Disposition"] == "attachment"
    assert r.text == "This is a test file for the downloading purpose\n"
