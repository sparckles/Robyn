import pytest

from robyn.robyn import Response


class A:
    pass


bad_bodies = [
    None,
    1,
    True,
    A,
    {"body": "OK"},
    ["OK", b"OK"],
    Response(
        status_code=200,
        headers={},
        body=b"OK",
    ),
]

good_bodies = ["OK", b"OK"]


@pytest.mark.parametrize("body", bad_bodies)
def test_bad_body_types(body):
    with pytest.raises(ValueError):
        _ = Response(
            status_code=200,
            headers={},
            body=body,
        )


@pytest.mark.parametrize("body", good_bodies)
def test_good_body_types(body):
    _ = Response(
        status_code=200,
        headers={},
        body=body,
    )
