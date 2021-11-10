import requests

BASE_URL = "http://127.0.0.1:5000"

def test_put(session):
    res = requests.put(f"{BASE_URL}/put")
    assert (res.status_code == 200)
    assert res.text=="PUT Request"

def test_put_with_param(session):
    res = requests.put(f"{BASE_URL}/put_with_body", data = {
        "hello": "world"
    })

    assert (res.status_code == 200)
    assert res.text=="hello=world"
