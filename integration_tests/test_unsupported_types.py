import pytest

from robyn.robyn import Response


def test_bad_body_types():
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

    for body in bad_bodies:
        with pytest.raises(ValueError):
            _ = Response(
                status_code=200,
                headers={},
                body=body,
            )


def test_good_body_types():
    good_bodies = ["OK", b"OK"]

    for body in good_bodies:
        _ = Response(
            status_code=200,
            headers={},
            body=body,
        )
