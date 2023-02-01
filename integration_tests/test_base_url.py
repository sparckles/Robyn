import os

import requests


def test_default_url_index_request(default_session):
    BASE_URL = "http://127.0.0.1:8080"
    res = requests.get(f"{BASE_URL}")
    assert res.status_code == 200


def test_local_index_request(session):
    BASE_URL = "http://127.0.0.1:8080"
    res = requests.get(f"{BASE_URL}")
    assert os.getenv("ROBYN_URL") == "127.0.0.1"
    assert res.status_code == 200


def test_global_index_request(global_session):
    BASE_URL = "http://0.0.0.0:8080"
    res = requests.get(f"{BASE_URL}")
    assert os.getenv("ROBYN_URL") == "0.0.0.0"
    assert res.status_code == 200


def test_dev_index_request(dev_session):
    BASE_URL = "http://127.0.0.1:8081"
    res = requests.get(f"{BASE_URL}")
    assert os.getenv("ROBYN_PORT") == "8081"
    assert res.status_code == 200
