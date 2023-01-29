import requests

BASE_URL = "http://127.0.0.1:8080"


def test_binary_output_sync(session):
    r = requests.get(f"{BASE_URL}/binary_output_sync")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/octet-stream"
    assert r.text == "OK"


def test_binary_output_response_sync(session):
    r = requests.get(f"{BASE_URL}/binary_output_response_sync")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/octet-stream"
    assert r.text == "OK"


def test_binary_output_async(session):
    r = requests.get(f"{BASE_URL}/binary_output_async")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/octet-stream"
    assert r.text == "OK"


def test_binary_output_response_async(session):
    r = requests.get(f"{BASE_URL}/binary_output_response_async")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/octet-stream"
    assert r.text == "OK"
