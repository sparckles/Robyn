"""Tests for the convenience request type aliases (issue #1077).

``RequestMethod``, ``RequestBody`` and ``RequestURL`` describe the runtime types
of ``request.method``, ``request.body`` and ``request.url`` so that handler code
can be type-checked. They must be importable both from the top-level ``robyn``
package and from ``robyn.types``.
"""

import typing

from robyn.robyn import Url


def test_request_types_importable_from_package():
    from robyn import RequestBody, RequestMethod, RequestURL

    assert RequestMethod is not None
    assert RequestBody is not None
    assert RequestURL is not None


def test_request_types_importable_from_types_module():
    # Same objects regardless of import path.
    from robyn import RequestBody as PkgRequestBody
    from robyn import RequestMethod as PkgRequestMethod
    from robyn import RequestURL as PkgRequestURL
    from robyn.types import RequestBody, RequestMethod, RequestURL

    assert RequestMethod is PkgRequestMethod
    assert RequestBody is PkgRequestBody
    assert RequestURL is PkgRequestURL


def test_request_method_literal_values():
    from robyn import RequestMethod

    args = set(typing.get_args(RequestMethod))
    assert {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}.issubset(args)


def test_request_body_is_str_or_bytes():
    from robyn import RequestBody

    assert set(typing.get_args(RequestBody)) == {str, bytes}


def test_request_url_is_url():
    from robyn import RequestURL

    assert RequestURL is Url
