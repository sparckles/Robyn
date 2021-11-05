import requests

BASE_URL = "http://127.0.0.1:5000"

def test_post(session):
    res = requests.post(f"{BASE_URL}/post")
    assert (res.status_code == 200)
    assert res.text=="POST Request"

def test_post_with_param(session):
    res = requests.post(f"{BASE_URL}/post_with_body", data = {
        "hello": "world"
    })
    assert res.text=="hello=world"
    assert (res.status_code == 200)


def test_jsonify_request(session):
    res = requests.post(f"{BASE_URL}/jsonify/123")
    assert(res.status_code == 200)
    assert res.json()=={"hello":"world"}

