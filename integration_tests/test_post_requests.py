from http_methods_helpers import post


def test_post(session):
    res = post("/sync/dict")
    assert res.text == "sync dict post"
    assert "sync" in res.headers
    assert res.headers["sync"] == "dict"
    res = post("/async/dict")
    assert res.text == "async dict post"
    assert "async" in res.headers
    assert res.headers["async"] == "dict"


def test_post_with_param(session):
    res = post("/sync/body", data={"hello": "world"})
    assert res.text == "hello=world"
    res = post("/async/body", data={"hello": "world"})
    assert res.text == "hello=world"
