import requests

BASE_URL = "http://127.0.0.1:5000"

def test_delete(session):
    res = requests.delete(f"{BASE_URL}/delete")
    assert (res.status_code == 200)
    assert res.text=="DELETE Request"

def test_delete_with_param(session):
    res = requests.delete(f"{BASE_URL}/delete_with_body", data = {
        "hello": "world"
    })
    assert (res.status_code == 200)
    assert res.text=="hello=world"

