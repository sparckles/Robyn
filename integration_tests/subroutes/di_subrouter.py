from robyn import Request, SubRouter

di_subrouter = SubRouter(__file__, "/di_subrouter")
GLOBAL_DEPENDENCY = "GLOBAL DEPENDENCY OVERRIDE"
ROUTER_DEPENDENCY = "ROUTER DEPENDENCY"
di_subrouter.inject_global(GLOBAL_DEPENDENCY=GLOBAL_DEPENDENCY)
di_subrouter.inject(ROUTER_DEPENDENCY=ROUTER_DEPENDENCY)


@di_subrouter.get("/subrouter_router_di")
def sync_subrouter_route_dependency(r: Request, router_dependencies, global_dependencies):
    return router_dependencies["ROUTER_DEPENDENCY"]


@di_subrouter.get("/subrouter_global_di")
def sync_subrouter_global_dependency(global_dependencies):
    return global_dependencies["GLOBAL_DEPENDENCY"]


# ===== Authentication =====


@di_subrouter.get("/subrouter_router_di/sync/auth", auth_required=True)
def sync_subrouter_auth(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@di_subrouter.get("/subrouter_router_di/async/auth", auth_required=True)
async def async_subrouter_auth(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"
