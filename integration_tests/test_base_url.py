import requests


def test_local_index_request(session):
    BASE_URL = "http://127.0.0.1:5000"
    res = requests.get(f"{BASE_URL}")
    assert(res.status_code == 200)

def test_global_index_request(global_session):
    BASE_URL = "http://0.0.0.0:5000"
    res = requests.get(f"{BASE_URL}")
    assert(res.status_code == 200)

