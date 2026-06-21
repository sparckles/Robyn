"""
First-party signed-cookie sessions for Robyn.

The session is stored entirely on the client inside a tamper-proof signed
cookie (an HMAC-SHA256 signature over a base64url-encoded JSON payload), so no
server-side store is required. Signing protects the payload against
*modification*, not against *reading* — the data is encoded, not encrypted, so
never put secrets in the session.

Enable it once on the app::

    app.configure_sessions(secret_key="change-me")

and read or write the session from inside any request handler via
``request.session`` (a dict-like :class:`Session`)::

    @app.get("/")
    def index(request):
        request.session["views"] = request.session.get("views", 0) + 1
        return f"views: {request.session['views']}"

The cookie is (re)written automatically after the handler runs, but only when
the session was actually modified. The :class:`Session` is shared by reference
across the request phases through ``request.session``, so this works on every
supported Python version with no ``contextvars`` dependency.
"""

import base64
import hashlib
import hmac
import json
import logging
import math
import time
from collections.abc import MutableMapping
from typing import Any, Optional

_logger = logging.getLogger(__name__)

# Largest cookie most browsers will store (4 KB) minus headroom for the cookie
# name and attributes. Sessions larger than this are silently dropped by the
# browser, so we warn instead of failing.
_MAX_COOKIE_SIZE = 4093

__all__ = [
    "Session",
    "SessionManager",
]


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class _Signer:
    """itsdangerous-style HMAC-SHA256 signer, stdlib only."""

    def __init__(self, secret_key: str, salt: bytes = b"robyn.session") -> None:
        # Derive a fixed-length key so arbitrary secret_key lengths are fine.
        self._key = hashlib.sha256(salt + secret_key.encode("utf-8")).digest()

    def _signature(self, value: bytes) -> str:
        return _b64encode(hmac.new(self._key, value, hashlib.sha256).digest())

    def sign(self, payload: bytes) -> str:
        value = _b64encode(payload)
        return f"{value}.{self._signature(value.encode('ascii'))}"

    def unsign(self, signed: str) -> Optional[bytes]:
        """Verify and decode ``signed``; return the payload bytes, or None if invalid."""
        try:
            value, signature = signed.rsplit(".", 1)
        except ValueError:
            return None
        expected = self._signature(value.encode("ascii"))
        # Constant-time comparison to avoid signature-timing leaks.
        if not hmac.compare_digest(expected, signature):
            return None
        try:
            return _b64decode(value)
        except (ValueError, base64.binascii.Error):
            return None


class Session(MutableMapping):
    """
    A dict-like session object.

    Behaves like a normal ``dict`` (``session["k"] = v``, ``session.get("k")``,
    ``del session["k"]``, ``in``, iteration, ``update``, ``pop`` ...).

    Robyn re-writes the cookie after the handler only when the session changed.
    Top-level mutations flip :attr:`modified` directly; *nested* mutations (e.g.
    ``session["items"].append(x)``) are still caught because :meth:`is_modified`
    also compares the current contents against a snapshot taken at load time. You
    can also force a write by setting ``session.modified = True``.
    """

    __slots__ = ("_data", "modified", "_snapshot")

    def __init__(self, data: Optional[dict] = None) -> None:
        self._data: dict = dict(data) if data else {}
        #: True once the session has been explicitly mutated during this request.
        self.modified: bool = False
        # Canonical snapshot of the loaded data, used to detect nested mutations
        # that bypass __setitem__/__delitem__.
        self._snapshot: Optional[str] = self._canonical()

    def _canonical(self) -> Optional[str]:
        """Order-independent JSON of the data, or None if it is not serializable."""
        try:
            return json.dumps(self._data, sort_keys=True, separators=(",", ":"))
        except TypeError:
            # Non-serializable content -> treat as changed so save() runs and
            # surfaces a clear error rather than silently dropping the write.
            return None

    def is_modified(self) -> bool:
        """True if the session changed this request (top-level or nested)."""
        if self.modified:
            return True
        current = self._canonical()
        return current is None or current != self._snapshot

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.modified = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self.modified = True

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def clear(self) -> None:
        """Remove all data from the session (marks it modified)."""
        if self._data:
            self.modified = True
        self._data.clear()

    def __repr__(self) -> str:
        return f"Session({self._data!r})"


class SessionManager:
    """
    Serializes, signs, reads, and writes :class:`Session` cookies.

    This is the lower-level primitive behind :meth:`Robyn.configure_sessions`.
    It can also be used directly (``load(request)`` / ``save(session, response)``)
    when you want explicit control instead of the automatic middleware.
    """

    def __init__(
        self,
        secret_key: str,
        *,
        cookie_name: str = "session",
        max_age: Optional[int] = 14 * 24 * 60 * 60,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str = "Lax",
    ) -> None:
        if not secret_key:
            raise ValueError("configure_sessions() requires a non-empty secret_key")
        self._signer = _Signer(secret_key)
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.path = path
        self.domain = domain
        self.secure = secure
        self.http_only = http_only
        self.same_site = _normalize_same_site(same_site)
        # Browsers reject SameSite=None cookies that are not also Secure, which
        # silently breaks the session. Fail loudly at configuration time instead.
        if self.same_site == "None" and not self.secure:
            raise ValueError("same_site='None' requires secure=True (browsers reject SameSite=None cookies without the Secure attribute)")

    # -- serialization ---------------------------------------------------

    def dumps(self, session: Session) -> str:
        """Serialize and sign ``session`` into a cookie value."""
        envelope: dict = {"d": dict(session)}
        if self.max_age is not None:
            envelope["exp"] = int(time.time()) + self.max_age
        try:
            payload = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        except TypeError as exc:
            raise TypeError(f"Session data must be JSON-serializable to fit in a signed cookie: {exc}") from exc
        return self._signer.sign(payload)

    def loads(self, raw: str) -> Session:
        """Verify and decode a cookie value into a :class:`Session` (empty if invalid/expired)."""
        payload = self._signer.unsign(raw)
        if payload is None:
            return Session()
        try:
            envelope = json.loads(payload)
        except ValueError:
            return Session()
        if not isinstance(envelope, dict) or not isinstance(envelope.get("d"), dict):
            return Session()
        exp = envelope.get("exp")
        # exp must be a finite number. A non-numeric value, a bool, or a
        # non-finite float (NaN/Infinity — which json.loads accepts and which
        # slip past a plain ``exp < now`` comparison) is treated as invalid
        # rather than raising or being trusted as a never-expiring session.
        if exp is not None and (not isinstance(exp, (int, float)) or isinstance(exp, bool) or not math.isfinite(exp) or exp < time.time()):
            return Session()
        return Session(envelope["d"])

    # -- request/response integration ------------------------------------

    def load(self, request) -> Session:
        """Build the :class:`Session` for ``request`` from its signed cookie."""
        raw = _read_cookie(request, self.cookie_name)
        if raw is None:
            return Session()
        return self.loads(raw)

    def save(self, session: Session, response) -> None:
        """Write ``session`` back onto ``response`` as a cookie, if it changed."""
        if not session.is_modified():
            return
        if len(session) == 0:
            # Session was emptied/cleared -> expire the cookie in the browser.
            response.set_cookie(
                key=self.cookie_name,
                value="",
                path=self.path,
                domain=self.domain,
                max_age=0,
                secure=self.secure,
                http_only=self.http_only,
                same_site=self.same_site,
            )
            return
        value = self.dumps(session)
        if len(value) > _MAX_COOKIE_SIZE:
            _logger.warning(
                "Robyn session cookie is %d bytes, larger than the ~4KB most browsers store; it may be dropped. Store less data in the session.",
                len(value),
            )
        response.set_cookie(
            key=self.cookie_name,
            value=value,
            path=self.path,
            domain=self.domain,
            max_age=self.max_age,
            secure=self.secure,
            http_only=self.http_only,
            same_site=self.same_site,
        )


def _normalize_same_site(value: Optional[str]) -> Optional[str]:
    """Normalize SameSite to the capitalization Robyn's cookie layer expects."""
    if value is None:
        return None
    normalized = value.strip().capitalize()
    if normalized not in ("Strict", "Lax", "None"):
        raise ValueError(f"same_site must be one of 'Strict', 'Lax', 'None' (got {value!r})")
    return normalized


def _read_cookie(request, name: str) -> Optional[str]:
    """Extract a single cookie value from the request's ``Cookie`` header."""
    header = request.headers.get("Cookie")
    if not header:
        return None
    for part in header.split(";"):
        key, _, value = part.partition("=")
        if key.strip() == name:
            return value.strip()
    return None
