from robyn import Robyn, SubRouter

#Tests nested subrouter prefixes are consistent with websocket routes
def test_subrouter_nested_prefixes():
    # Create main app
    app = Robyn(__file__)

    # Create middle router (b) with prefix /bbb
    router_b = SubRouter(__file__, prefix="/bbb")

    # Create nested router (c) with prefix /ccc
    router_c = SubRouter(__file__, prefix="/ccc")

    # Define HTTP route in router_c
    @router_c.get("/hello")
    def hello_from_c():
        return {"message": "Hello from router_c"}

    # Define WebSocket route in router_c
    @router_c.websocket("/ws")
    async def ws_from_c(websocket):
        await websocket.accept()
        await websocket.send_text("Hello from WebSocket in router_c")
        await websocket.close()

    # Include router_c into router_b
    router_b.include_router(router_c)

    # Include router_b into main app
    app.include_router(router_b)

    # List registered  HTTP routes
    http_routes = []
    for route in app.router.routes:
        http_routes.append(route.route)

    # List registered Websocket routes
    websocket_routes = list(app.web_socket_router.routes.keys())

    # HTTP and WebSocket routes should both be correctly prefixed
    assert "/ccc/hello" in http_routes
    assert "/bbb/ccc/ws" in websocket_routes
    