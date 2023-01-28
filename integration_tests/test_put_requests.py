from utils import put


def test_put(session):
    res = put("/sync/dict")
    assert res.text == "sync dict put"
    assert "sync" in res.headers
    assert res.headers["sync"] == "dict"
    res = put("/async/dict")
    assert res.text == "async dict put"
    assert "async" in res.headers
    assert res.headers["async"] == "dict"


def test_put_with_param(session):
    res = put("/sync/body", data={"hello": "world"})
    assert res.text == "hello=world"
    res = put("/async/body", data={"hello": "world"})
    assert res.text == "hello=world"
