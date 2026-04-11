from robyn import Robyn


def test_status_code_on_post(tmp_path):
    app = Robyn(__file__)

    @app.post("/items", status_code=201)
    async def create_item():
        return {"id": 1}

    routes = app.router.get_routes()
    assert len(routes) == 1
    assert routes[0].default_status_code == 201


def test_status_code_default_none(tmp_path):
    app = Robyn(__file__)

    @app.get("/items")
    async def list_items():
        return []

    routes = app.router.get_routes()
    assert routes[0].default_status_code is None
