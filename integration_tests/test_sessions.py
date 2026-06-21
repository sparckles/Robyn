import requests

BASE_URL = "http://127.0.0.1:8080"
COOKIE_NAME = "robyn_session"
TIMEOUT = 5  # seconds; keep tests from hanging if the server becomes unresponsive


def test_session_is_empty_by_default(session):
    r = requests.get(f"{BASE_URL}/sessions/get", timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.json()["value"] is None
    # No session cookie is set when nothing is stored.
    assert COOKIE_NAME not in r.cookies


def test_session_persists_across_requests(session):
    client = requests.Session()

    r = client.post(f"{BASE_URL}/sessions/set", json={"value": "hello"}, timeout=TIMEOUT)
    assert r.json()["stored"] == "hello"
    assert COOKIE_NAME in r.cookies  # cookie written on modification

    # A later request on the same client sees the stored value.
    r = client.get(f"{BASE_URL}/sessions/get", timeout=TIMEOUT)
    assert r.json()["value"] == "hello"


def test_session_counter_increments_per_client(session):
    client = requests.Session()
    counts = [client.get(f"{BASE_URL}/sessions/counter", timeout=TIMEOUT).json()["count"] for _ in range(3)]
    assert counts == [1, 2, 3]

    # A fresh client starts its own session from scratch.
    other = requests.Session()
    assert other.get(f"{BASE_URL}/sessions/counter", timeout=TIMEOUT).json()["count"] == 1


def test_session_cookie_is_http_only(session):
    client = requests.Session()
    r = client.post(f"{BASE_URL}/sessions/set", json={"value": "x"}, timeout=TIMEOUT)
    set_cookie = r.headers.get("Set-Cookie", "")
    assert COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie


def test_tampered_session_cookie_is_rejected(session):
    client = requests.Session()
    # Establish a session (count = 1).
    client.get(f"{BASE_URL}/sessions/counter", timeout=TIMEOUT)
    original = client.cookies.get(COOKIE_NAME)
    assert original is not None

    # Flip the tail of the signed value; the HMAC no longer matches.
    tampered = original[:-3] + ("aaa" if not original.endswith("aaa") else "bbb")
    r = requests.get(f"{BASE_URL}/sessions/counter", cookies={COOKIE_NAME: tampered}, timeout=TIMEOUT)
    # Tampered cookie -> treated as empty session -> counter restarts at 1.
    assert r.json()["count"] == 1


def test_session_clear_removes_data(session):
    client = requests.Session()
    client.post(f"{BASE_URL}/sessions/set", json={"value": "to-be-cleared"}, timeout=TIMEOUT)
    assert client.get(f"{BASE_URL}/sessions/get", timeout=TIMEOUT).json()["value"] == "to-be-cleared"

    client.get(f"{BASE_URL}/sessions/clear", timeout=TIMEOUT)
    assert client.get(f"{BASE_URL}/sessions/get", timeout=TIMEOUT).json()["value"] is None
