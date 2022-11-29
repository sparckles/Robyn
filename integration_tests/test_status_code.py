import requests

BASE_URL = "http://127.0.0.1:5000"


def test_404_status_code(session):
    res = requests.get(f"{BASE_URL}/404")
    assert res.status_code == 404


def test_404_post_request_status_code(session):
    r = requests.post(f"{BASE_URL}/404")
    assert r.status_code == 404


def test_307_get_request(session):
    r = requests.get(f"{BASE_URL}/redirect")
    assert r.text == "This is the redirected route"


def test_int_status_code(session):
    r = requests.get(f"{BASE_URL}/int_status_code")
    assert r.status_code == 202
