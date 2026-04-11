from robyn import Robyn


def test_deprecated_route():
    app = Robyn(__file__)

    @app.get("/old-endpoint", deprecated=True)
    async def old_handler():
        return "old"

    routes = app.router.get_routes()
    assert routes[0].deprecated is True


def test_include_in_schema_false():
    app = Robyn(__file__)

    @app.get("/health", include_in_schema=False)
    async def health():
        return "ok"

    routes = app.router.get_routes()
    assert routes[0].include_in_schema is False


def test_defaults():
    app = Robyn(__file__)

    @app.get("/normal")
    async def normal():
        return "normal"

    routes = app.router.get_routes()
    assert routes[0].deprecated is False
    assert routes[0].include_in_schema is True
