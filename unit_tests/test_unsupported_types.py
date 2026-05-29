import pytest

from robyn.robyn import Headers, Response


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
        headers=Headers({}),
        description=b"OK",
    ),
]

good_bodies = ["OK", b"OK"]


@pytest.mark.parametrize("description", bad_bodies)
def test_bad_body_types(description):
    with pytest.raises(ValueError):
        _ = Response(
            status_code=200,
            headers=Headers({}),
            description=description,
        )


@pytest.mark.parametrize("description", good_bodies)
def test_good_body_types(description):
    response = Response(
        status_code=200,
        headers=Headers({}),
        description=description,
    )

    assert response.description == description


@pytest.mark.parametrize("description", good_bodies)
def test_good_body_types_with_default_headers(description):
    response = Response(
        status_code=200,
        description=description,
    )

    assert response.description == description


@pytest.mark.parametrize("body", good_bodies)
def test_good_body_alias_types(body):
    response = Response(
        status_code=200,
        headers=Headers({}),
        body=body,
    )

    assert response.description == body


@pytest.mark.parametrize("body", bad_bodies)
def test_bad_body_alias_types(body):
    with pytest.raises(ValueError):
        _ = Response(
            status_code=200,
            headers=Headers({}),
            body=body,
        )


def test_body_alias_cannot_be_combined_with_description():
    with pytest.raises(TypeError):
        _ = Response(
            status_code=200,
            headers=Headers({}),
            description="OK",
            body="OK",
        )


def test_body_alias_cannot_be_combined_with_positional_description():
    with pytest.raises(TypeError):
        _ = Response(
            200,
            Headers({}),
            "OK",
            body="OK",
        )


def test_positional_description_cannot_be_combined_with_keyword_description():
    with pytest.raises(TypeError):
        _ = Response(
            200,
            Headers({}),
            "OK",
            description="OK",
        )


def test_body_alias_can_use_default_headers():
    response = Response(status_code=200, body="OK")

    assert response.description == "OK"


def test_body_alias_can_use_none_headers():
    response = Response(status_code=200, headers=None, body="OK")

    assert response.description == "OK"
