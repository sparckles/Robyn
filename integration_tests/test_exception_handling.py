import pytest
from helpers.http_methods_helpers import get


@pytest.mark.benchmark
def test_exception_handling(session):
    r = get("/sync/exception", expected_status_code=500)
    assert r.text == "error msg: value error"
