import requests

BASE_URL = "http://127.0.0.1:8080"


def test_404_status_code(session):
    res = requests.get(f"{BASE_URL}/404")
    assert res.status_code == 404


def test_404_post_request_status_code(session):
    r = requests.post(f"{BASE_URL}/404")
    assert r.status_code == 404


def test_404_not_found(session):
    r = requests.get(f"{BASE_URL}/actually_not_found_route")
    assert r.status_code == 404
    assert r.text == "Not found"


def test_307_get_request(session):
    r = requests.get(f"{BASE_URL}/redirect")
    assert r.text == "This is the redirected route"


def test_int_status_code(session):
    r = requests.get(f"{BASE_URL}/int_status_code")
    assert r.status_code == 202


def test_sync_500_internal_server_error(session):
    r = requests.get(f"{BASE_URL}/sync/raise")
    assert r.status_code == 500


def test_async_500_internal_server_error(session):
    r = requests.get(f"{BASE_URL}/async/raise")
    assert r.status_code == 500
