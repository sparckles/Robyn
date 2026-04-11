from robyn.exceptions import HTTPException


def test_http_exception_default():
    exc = HTTPException(404)
    assert exc.status_code == 404
    assert exc.detail == "Not Found"
    assert exc.headers == {}


def test_http_exception_custom_detail():
    exc = HTTPException(403, detail="Go away")
    assert exc.detail == "Go away"


def test_http_exception_with_headers():
    exc = HTTPException(
        401,
        detail="Token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    assert exc.status_code == 401
    assert exc.detail == "Token expired"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_http_exception_str():
    exc = HTTPException(500, detail="Internal error")
    assert str(exc) == "500: Internal error"


def test_http_exception_repr():
    exc = HTTPException(400, detail="Bad input")
    assert "HTTPException" in repr(exc)
    assert "400" in repr(exc)
