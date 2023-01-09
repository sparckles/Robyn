import requests

BASE_URL = "http://127.0.0.1:8080"


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


def test_request_headers(session):
    r = requests.get(f"{BASE_URL}/request_headers")
    assert r.status_code == 200
    assert r.text == "This is a regular response"
    assert "Header" in r.headers
    assert r.headers["Header"] == "header_value"


def test_const_request(session):
    r = requests.get(f"{BASE_URL}/const_request")
    assert "Hello world" in r.text
    assert r.status_code == 200


def test_const_request_json(session):
    r = requests.get(f"{BASE_URL}/const_request_json")
    assert r.status_code == 200
    assert r.json() == {"hello": "world"}


def test_const_request_headers(session):
    r = requests.get(f"{BASE_URL}/const_request_headers")
    assert r.status_code == 200
    assert "Header" in r.headers
    assert r.headers["Header"] == "header_value"


def test_response_type(session):
    r = requests.get(f"{BASE_URL}/types/response")
    assert r.status_code == 200
    assert r.text == "OK"


def test_str_type(session):
    r = requests.get(f"{BASE_URL}/types/str")
    assert r.status_code == 200
    assert r.text == "OK"


def test_int_type(session):
    r = requests.get(f"{BASE_URL}/types/int")
    assert r.status_code == 200
    assert r.text == "0"


def test_async_response_type(session):
    r = requests.get(f"{BASE_URL}/async/types/response")
    assert r.status_code == 200
    assert r.text == "OK"


def test_async_str_type(session):
    r = requests.get(f"{BASE_URL}/async/types/str")
    assert r.status_code == 200
    assert r.text == "OK"


def test_async_int_type(session):
    r = requests.get(f"{BASE_URL}/async/types/int")
    assert r.status_code == 200
    assert r.text == "0"
