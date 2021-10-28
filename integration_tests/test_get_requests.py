import requests

def test_index_request(session):
    res = requests.get("http://127.0.0.1:5000/")
    assert(res.status_code == 200)

def test_jsonify(session):
    r = requests.get("http://127.0.0.1:5000/jsonify")
    assert r.json()=={"hello":"world"}
    assert r.status_code==200

def test_html(session):
    r = requests.get("http://127.0.0.1:5000/test/123")
    assert "Hello world. How are you?" in r.text

