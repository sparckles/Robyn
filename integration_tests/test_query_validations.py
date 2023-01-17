import requests

BASE_URL = "http://127.0.0.1:5000"
CORRECT_BODY = {
    "a": 5,
    "b": "hello"
}
INCORRECT_BODY = {
    "a": 5,
    "b": 6
}

CORRECT_BODY_COMPLEX = {
    "a": 5,
    "b": "hello",
    "c": {
	    "f": {"f": 7, "g": 8},
	    "special": "Nicer"
        }
}

INCORRECT_BODY_COMPLEX = {
    "a": 5,
    "b": "hello",
    "c": {
	    "f": {"f": 7, "g": "str"},
	    "special": "Nicer"
        }   
}

CORRECT_BODY_COMPLEX_NODEFAULT = {
    "a": 5,
    "b": "hello",
    "c": {
	    "f": {"f": 7, "g": 8}
        }
}

CORRECT_BODY_COMPLEX_NODEFAULT_RESULT = {
    "a": 5,
    "b": "hello",
    "c": {
	    "f": {"f": 7, "g": 8},
        "special": "Nice"
        }
}

CORRECT_BODY_COMPLEX_FORWARDREF = {
    "a": 5,
    "b": "hello",
    "c": {
        "a": 5,
	    "b": {"c": 7, "d": "Hello"}
        }
}

INCORRECT_BODY_COMPLEX_FORWARDREF = {
    "a": 5,
    "b": "hello",
    "c": {
        "a": 5,
	    "b": {"c": 7, "d": 9}
        }
}

def test_post_simple_correct(session):
    res = requests.post(f"{BASE_URL}/query_validation", json=CORRECT_BODY)
    assert res.status_code == 200
    assert res.json() == CORRECT_BODY

def test_post_simple_incorrect(session):
    res = requests.post(f"{BASE_URL}/query_validation", json=INCORRECT_BODY)
    assert res.status_code == 500

def test_post_complex_correct(session):
    res = requests.post(f"{BASE_URL}/query_validation_complex", json=CORRECT_BODY_COMPLEX)
    assert res.status_code == 200
    assert res.json() == CORRECT_BODY_COMPLEX

def test_post_complex_incorrect(session):
    res = requests.post(f"{BASE_URL}/query_validation_complex", json=INCORRECT_BODY_COMPLEX)
    assert res.status_code == 500

def test_post_complex_default_correct(session):
    res = requests.post(f"{BASE_URL}/query_validation_complex", json=CORRECT_BODY_COMPLEX_NODEFAULT)
    assert res.status_code == 200
    assert res.json() == CORRECT_BODY_COMPLEX_NODEFAULT_RESULT

def test_post_complex_forwardref_correct(session):
    res = requests.post(f"{BASE_URL}/query_validation_forwardref", json=CORRECT_BODY_COMPLEX_FORWARDREF)
    assert res.status_code == 200
    assert res.json() == CORRECT_BODY_COMPLEX_FORWARDREF

def test_post_complex_forwardref_incorrect(session):
    res = requests.post(f"{BASE_URL}/query_validation_forwardref", json=INCORRECT_BODY_COMPLEX_FORWARDREF)
    assert res.status_code == 500
