from __future__ import annotations

from robyn.robyn import Headers, QueryParams
from robyn.ws import _signature_params


def test_postponed_annotations_are_resolved():
    def handler(websocket, upgrade_headers: Headers, params: QueryParams, page: int = 1):
        pass

    params = _signature_params(handler)

    assert params["upgrade_headers"].annotation is Headers
    assert params["params"].annotation is QueryParams
    assert params["page"].annotation is int


def test_unresolvable_annotation_falls_back_to_raw_signature():
    def handler(websocket, value: DoesNotExist):  # noqa: F821
        pass

    assert _signature_params(handler)["value"].annotation == "DoesNotExist"
