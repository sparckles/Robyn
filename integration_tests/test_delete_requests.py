from utils import delete


def test_delete(session):
    res = delete("/sync/dict")
    assert res.text == "sync dict delete"
    assert "sync" in res.headers
    assert res.headers["sync"] == "dict"
    res = delete("/async/dict")
    assert res.text == "async dict delete"
    assert "async" in res.headers
    assert res.headers["async"] == "dict"


def test_delete_with_param(session):
    res = delete("/sync/body", data={"hello": "world"})
    assert res.text == "hello=world"
    res = delete("/async/body", data={"hello": "world"})
    assert res.text == "hello=world"
