from robyn import SubRouter, Request

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
