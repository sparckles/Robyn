import requests

BASE_URL = "http://127.0.0.1:5000"
CORRECT_BODY = {
    'a': 5,
    'b': "hello",
}
INCORRECT_BODY = {
    'a': 5,
    'b': 6,
}

def test_post_correct(session):
    res = requests.post(f"{BASE_URL}/query_validation", json=CORRECT_BODY)
    assert res.status_code == 200
    assert res.json() == CORRECT_BODY

def test_post_incorrect(session):
    res = requests.post(f"{BASE_URL}/query_validation", json=INCORRECT_BODY)
    assert res.status_code == 500
