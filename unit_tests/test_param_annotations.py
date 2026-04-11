from robyn.params import Query, Path, Header, Cookie


def test_query_param_defaults():
    q = Query(default=10, ge=1, le=100, description="Page size")
    assert q.default == 10
    assert q.required is False
    assert q.source == "query"
    assert q.description == "Page size"


def test_path_param_required():
    p = Path(description="User ID")
    assert p.required is True
    assert p.source == "path"


def test_header_param():
    h = Header(default=None, alias="X-Request-ID")
    assert h.alias == "X-Request-ID"
    assert h.source == "header"


def test_cookie_param():
    c = Cookie(default=None, description="Session token")
    assert c.source == "cookie"


def test_validate_gt():
    q = Query(gt=0)
    assert q.validate(5, "test") == 5
    try:
        q.validate(0, "test")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_validate_ge():
    q = Query(ge=1)
    assert q.validate(1, "test") == 1
    try:
        q.validate(0, "test")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_validate_le():
    q = Query(le=100)
    assert q.validate(100, "test") == 100
    try:
        q.validate(101, "test")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_validate_min_max_length():
    q = Query(min_length=3, max_length=10)
    assert q.validate("hello", "test") == "hello"
    try:
        q.validate("ab", "test")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_validate_pattern():
    q = Query(pattern=r"^\d{3}-\d{4}$")
    assert q.validate("123-4567", "test") == "123-4567"
    try:
        q.validate("invalid", "test")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_to_openapi_param():
    q = Query(default=1, ge=1, le=100, description="Page number")
    param = q.to_openapi_param("page", int)
    assert param["name"] == "page"
    assert param["in"] == "query"
    assert param["required"] is False
    assert param["schema"]["type"] == "integer"
    assert param["schema"]["minimum"] == 1
    assert param["schema"]["maximum"] == 100
    assert param["description"] == "Page number"


def test_repr():
    q = Query(default=5, description="Limit")
    r = repr(q)
    assert "Query" in r
    assert "5" in r


def test_required_validation():
    q = Query()
    try:
        q.validate(None, "test")
        assert False, "Should have raised"
    except ValueError:
        pass
