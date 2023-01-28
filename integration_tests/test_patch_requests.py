from utils import patch


def test_patch(session):
    res = patch("/sync/dict")
    assert res.text == "sync dict patch"
    assert "sync" in res.headers
    assert res.headers["sync"] == "dict"
    res = patch("/async/dict")
    assert res.text == "async dict patch"
    assert "async" in res.headers
    assert res.headers["async"] == "dict"


def test_patch_with_param(session):
    res = patch("/sync/body", data={"hello": "world"})
    assert res.text == "hello=world"
    res = patch("/async/body", data={"hello": "world"})
    assert res.text == "hello=world"
