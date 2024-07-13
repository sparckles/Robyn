from robyn import SubRouter, Request

# Define the main router for nested routes
main_nest = SubRouter(__file__, "/main-nest")

# Define nested routers up to 5 levels
nested_router_1 = SubRouter(__file__, "/nested-1")
nested_router_2 = SubRouter(__file__, "/nested-2")
nested_router_3 = SubRouter(__file__, "/nested-3")
nested_router_4 = SubRouter(__file__, "/nested-4")
nested_router_5 = SubRouter(__file__, "/nested-5")

# Include routers inside each other to create nesting
main_nest.include_router(nested_router_1)
nested_router_1.include_router(nested_router_2)
nested_router_2.include_router(nested_router_3)
nested_router_3.include_router(nested_router_4)
nested_router_4.include_router(nested_router_5)


@nested_router_5.get("/nested-route-5")
def nested_route_example_5(request: Request):
    """
    Example route inside the nested router.
    """
    return "This is a route inside nested_router_5."


@nested_router_4.get("/nested-route-4")
def nested_route_example_4(request: Request):
    """
    Example route inside the nested router.
    """
    return "This is a route inside nested_router_4."


@nested_router_3.get("/nested-route-3")
def nested_route_example_3(request: Request):
    """
    Example route inside the nested router.
    """
    return "This is a route inside nested_router_3."


@nested_router_2.get("/nested-route-2", auth_required=True)
def nested_route_example_2(request: Request):
    """
    Example route inside the nested router.
    """
    return "This is a route inside nested_router_2."
