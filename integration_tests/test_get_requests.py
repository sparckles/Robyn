from requests import Response

from http_methods_helpers import get


def test_param(session):
    r = get("/sync/param/1")
    assert r.text == "1"
    r = get("/sync/param/12345")
    assert r.text == "12345"
    r = get("/async/param/1")
    assert r.text == "1"
    r = get("/async/param/12345")
    assert r.text == "12345"


def test_serve_html(session):
    def check_response(r: Response):
        assert r.text.startswith("<!DOCTYPE html>")
        assert "Hello world. How are you?" in r.text

    check_response(get("/sync/serve/html"))
    check_response(get("/async/serve/html"))


def test_template(session):
    def check_response(r: Response):
        assert r.text.startswith("\n\n<!DOCTYPE html>")
        assert "Jinja2" in r.text
        assert "Robyn" in r.text

    check_response(get("/sync/template"))
    check_response(get("/async/template"))


def test_queries(session):
    r = get("/sync/queries?hello=robyn")
    assert r.json() == {"hello": "robyn"}

    r = get("/sync/queries")
    assert r.json() == {}

    r = get("/async/queries?hello=robyn")
    assert r.json() == {"hello": "robyn"}

    r = get("/async/queries")
    assert r.json() == {}
