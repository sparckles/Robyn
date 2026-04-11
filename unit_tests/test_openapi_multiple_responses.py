from robyn import Robyn


def test_openapi_responses_registered():
    app = Robyn(__file__)

    @app.get(
        "/items/:id",
        openapi_responses={
            404: {"description": "Not found"},
            422: {"description": "Validation error"},
        },
    )
    async def get_item():
        return {}

    routes = app.router.get_routes()
    assert routes[0].openapi_responses is not None
    assert 404 in routes[0].openapi_responses


def test_openapi_responses_default_none():
    app = Robyn(__file__)

    @app.get("/items")
    async def list_items():
        return []

    routes = app.router.get_routes()
    assert routes[0].openapi_responses is None
