import requests

BASE_URL = "http://127.0.0.1:5000"


def test_404_status_code(session):
    res = requests.get(f"{BASE_URL}/404")
    assert res.status_code == 404


def test_404_post_request_status_code(session):
    r = requests.post(f"{BASE_URL}/404")
    assert r.status_code == 404
