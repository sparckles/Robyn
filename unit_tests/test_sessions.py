import pytest

from robyn.robyn import Headers, QueryParams, Request, Url
from robyn.session import Session, SessionManager, _read_cookie, _Signer

# --- helpers ---------------------------------------------------------------


class _FakeHeaders:
    def __init__(self, data: dict):
        self._data = {k.lower(): v for k, v in data.items()}

    def get(self, key: str):
        return self._data.get(key.lower())


class _FakeRequest:
    def __init__(self, headers: dict):
        self.headers = _FakeHeaders(headers)


class _FakeResponse:
    def __init__(self):
        self.cookies = {}

    def set_cookie(self, key, value, **kwargs):
        self.cookies[key] = (value, kwargs)


# --- signer ----------------------------------------------------------------


def test_signer_roundtrip():
    signer = _Signer("secret")
    assert signer.unsign(signer.sign(b"hello")) == b"hello"


def test_signer_rejects_tampered_payload():
    signer = _Signer("secret")
    signed = signer.sign(b"hello")
    value, sig = signed.rsplit(".", 1)
    tampered = f"{value}x.{sig}"
    assert signer.unsign(tampered) is None


def test_signer_rejects_wrong_key():
    signed = _Signer("key-a").sign(b"hello")
    assert _Signer("key-b").unsign(signed) is None


def test_signer_rejects_garbage():
    assert _Signer("k").unsign("not-a-signed-value") is None


# --- Session ---------------------------------------------------------------


def test_session_starts_unmodified():
    assert Session().modified is False
    assert Session({"a": 1}).modified is False


def test_session_mutation_marks_modified():
    s = Session()
    s["a"] = 1
    assert s.modified is True


def test_session_delete_marks_modified():
    s = Session({"a": 1})
    del s["a"]
    assert s.modified is True


def test_session_behaves_like_dict():
    s = Session({"a": 1})
    assert s["a"] == 1
    assert s.get("missing", "default") == "default"
    assert "a" in s
    assert list(s) == ["a"]
    assert len(s) == 1
    assert dict(s) == {"a": 1}


def test_session_update_and_pop_mark_modified():
    s = Session({"a": 1})
    s.update({"b": 2})
    assert s["b"] == 2 and s.modified
    s2 = Session({"a": 1})
    assert s2.pop("a") == 1 and s2.modified


def test_session_clear_marks_modified_only_when_nonempty():
    empty = Session()
    empty.clear()
    assert empty.modified is False
    full = Session({"a": 1})
    full.clear()
    assert full.modified is True and len(full) == 0


# --- SessionManager serialization -----------------------------------------


def test_manager_requires_secret_key():
    with pytest.raises(ValueError):
        SessionManager("")


def test_manager_roundtrip_preserves_data_and_resets_modified():
    manager = SessionManager("k")
    loaded = manager.loads(manager.dumps(Session({"user": "alice", "n": 3})))
    assert dict(loaded) == {"user": "alice", "n": 3}
    assert loaded.modified is False


def test_manager_rejects_tampered_cookie():
    manager = SessionManager("k")
    cookie = manager.dumps(Session({"admin": False}))
    tampered = cookie[:-3] + ("aaa" if not cookie.endswith("aaa") else "bbb")
    assert dict(manager.loads(tampered)) == {}


def test_manager_rejects_cookie_signed_with_other_key():
    foreign = SessionManager("other-key").dumps(Session({"admin": True}))
    assert dict(SessionManager("k").loads(foreign)) == {}


def test_manager_expired_session_is_empty():
    manager = SessionManager("k", max_age=-1)  # exp = now - 1 -> already expired
    assert dict(manager.loads(manager.dumps(Session({"a": 1})))) == {}


def test_manager_no_expiry_when_max_age_none():
    manager = SessionManager("k", max_age=None)
    assert dict(manager.loads(manager.dumps(Session({"a": 1})))) == {"a": 1}


def test_manager_non_serializable_raises():
    with pytest.raises(TypeError):
        SessionManager("k").dumps(Session({"bad": object()}))


# --- request/response integration -----------------------------------------


def test_read_cookie_parses_target_cookie():
    request = _FakeRequest({"Cookie": "a=1; robyn_session=abc.def; b=2"})
    assert _read_cookie(request, "robyn_session") == "abc.def"
    assert _read_cookie(request, "missing") is None


def test_read_cookie_no_header():
    assert _read_cookie(_FakeRequest({}), "robyn_session") is None


def test_load_reads_signed_cookie():
    manager = SessionManager("k", cookie_name="robyn_session")
    cookie = manager.dumps(Session({"x": 9}))
    request = _FakeRequest({"Cookie": f"robyn_session={cookie}"})
    assert dict(manager.load(request)) == {"x": 9}


def test_load_missing_cookie_returns_empty_session():
    assert dict(SessionManager("k").load(_FakeRequest({}))) == {}


def test_save_skips_unmodified_session():
    manager = SessionManager("k", cookie_name="robyn_session")
    response = _FakeResponse()
    manager.save(manager.load(_FakeRequest({})), response)
    assert response.cookies == {}


def test_save_writes_signed_cookie_when_modified():
    manager = SessionManager("k", cookie_name="robyn_session")
    response = _FakeResponse()
    session = Session()
    session["user"] = "bob"
    manager.save(session, response)
    assert "robyn_session" in response.cookies
    value, kwargs = response.cookies["robyn_session"]
    # round-trips back through the manager
    assert dict(manager.loads(value)) == {"user": "bob"}
    assert kwargs["http_only"] is True


def test_save_emptied_session_expires_cookie():
    manager = SessionManager("k", cookie_name="robyn_session")
    response = _FakeResponse()
    session = Session({"a": 1})
    session.clear()
    manager.save(session, response)
    value, kwargs = response.cookies["robyn_session"]
    assert value == "" and kwargs["max_age"] == 0


# --- same_site validation --------------------------------------------------


@pytest.mark.parametrize("value,expected", [("lax", "Lax"), ("STRICT", "Strict"), ("none", "None")])
def test_same_site_is_normalized(value, expected):
    # secure=True so the SameSite=None case is accepted (see guard below).
    assert SessionManager("k", same_site=value, secure=True).same_site == expected


def test_invalid_same_site_raises():
    with pytest.raises(ValueError):
        SessionManager("k", same_site="bogus")


def test_same_site_none_requires_secure():
    with pytest.raises(ValueError):
        SessionManager("k", same_site="None")  # secure defaults to False
    # Allowed when secure=True.
    assert SessionManager("k", same_site="None", secure=True).same_site == "None"


# --- change detection: nested mutations & exp guard ------------------------


def test_unmodified_session_is_not_modified():
    assert SessionManager("k").loads(SessionManager("k").dumps(Session({"a": 1}))).is_modified() is False


def test_nested_mutation_is_detected():
    session = Session({"items": [1]})
    assert session.is_modified() is False
    session["items"].append(2)  # bypasses __setitem__, modified flag stays False
    assert session.modified is False
    assert session.is_modified() is True


def test_nested_mutation_triggers_save():
    manager = SessionManager("k", cookie_name="robyn_session")
    session = Session({"items": [1]})
    session["items"].append(2)
    response = _FakeResponse()
    manager.save(session, response)
    assert "robyn_session" in response.cookies
    assert dict(manager.loads(response.cookies["robyn_session"][0])) == {"items": [1, 2]}


def test_key_reorder_is_not_a_false_positive():
    session = Session({"a": 1, "b": 2})
    # Rebuilding the same data in a different order must not count as a change.
    session._data = {"b": 2, "a": 1}
    assert session.is_modified() is False


def test_non_numeric_exp_is_treated_as_invalid():
    import json

    manager = SessionManager("k")
    forged = manager._signer.sign(json.dumps({"d": {"a": 1}, "exp": "whenever"}).encode("utf-8"))
    assert dict(manager.loads(forged)) == {}


# --- request.session attribute (real Rust Request) -------------------------


def _make_request(headers: dict):
    return Request(QueryParams(), Headers(headers), {}, "", "GET", Url("http", "testhost", "/"), {}, {}, None, None)


def test_request_session_attribute_defaults_to_none():
    assert _make_request({}).session is None


def test_request_session_roundtrips_through_manager():
    manager = SessionManager("k", cookie_name="robyn_session")

    # A handler would mutate request.session; emulate that here.
    request = _make_request({})
    request.session = Session({"n": 1})
    request.session["n"] += 1  # in-place mutation on the shared object

    response = _FakeResponse()
    manager.save(request.session, response)
    cookie_value = response.cookies["robyn_session"][0]

    # A later request carrying that cookie loads the same data back.
    next_request = _make_request({"Cookie": f"robyn_session={cookie_value}"})
    assert dict(manager.load(next_request)) == {"n": 2}
