import pytest
import requests

def test_jsonify():
    r = requests.get("http://web:5000/jsonify")
    assert r.json()=={"hello":"world"}
    assert r.status_code==200

def test_html():
    r = requests.get("http://web:5000/test")
    assert "Hello world. How are you?" in r.text

