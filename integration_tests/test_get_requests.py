import requests

BASE_URL = "http://127.0.0.1:5000"


def test_index_request(session):
    res = requests.get(f"{BASE_URL}")
    assert res.status_code == 200


def test_jsonify(session):
    r = requests.get(f"{BASE_URL}/jsonify")
    assert r.json() == {"hello": "world"}
    assert r.status_code == 200


def test_html(session):
    r = requests.get(f"{BASE_URL}/test/123")
    assert "Hello world. How are you?" in r.text


def test_jinja_template(session):
    r = requests.get(f"{BASE_URL}/template_render")
    assert "Jinja2" in r.text
    assert "Robyn" in r.text


def test_queries(session):
    r = requests.get(f"{BASE_URL}/query?hello=robyn")
    assert r.json() == {"hello": "robyn"}

    r = requests.get(f"{BASE_URL}/query")
    assert r.json() == {}


def test_const_request(session):
    r = requests.get(f"{BASE_URL}/const_request")
    assert "Hello world" in r.text
    assert r.status_code == 200


def test_const_request_json(session):
    r = requests.get(f"{BASE_URL}/const_request_json")
    assert r.status_code == 200
    assert r.json() == {"hello": "world"}
