from robyn import Robyn


def test_response_model_registered():
    app = Robyn(__file__)

    @app.get("/items", response_model=dict)
    async def get_items():
        return {"items": []}

    routes = app.router.get_routes()
    assert routes[0].response_model is dict


def test_response_model_default_none():
    app = Robyn(__file__)

    @app.get("/items")
    async def get_items():
        return []

    routes = app.router.get_routes()
    assert routes[0].response_model is None
