import requests

BASE_URL = "http://127.0.0.1:5000"


def test_patch(session):
    res = requests.patch(f"{BASE_URL}/patch")
    assert res.status_code == 200
    assert res.text == "PATCH Request"


def test_patch_with_param(session):
    res = requests.patch(f"{BASE_URL}/patch_with_body", data={"hello": "world"})
    assert res.status_code == 200
    assert res.text == "hello=world"
