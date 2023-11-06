from robyn import SubRouter

di_subrouter = SubRouter(__file__, "/subrouter")
GLOBAL_DEP_COLLISION = "global_dep_collision"

ROUTE_DEPENDENCY = "subrouter_route_dependency"
di_subrouter.inject(injected_argument='Override')
di_subrouter.inject(ROUTE_DEPENDENCY=ROUTE_DEPENDENCY)


@di_subrouter.get("/subrouter_route_dep_inject")
def sync_subrouter_route_dependency(request, router_dependencies):
    return f"ROUTER DEPENDENCY: {router_dependencies}"


@di_subrouter.get("/subrouter_global_dep_inject")
def sync_subrouter_global_dependency(request, global_dependencies):
    # return {"description": description}
    return "GLOBAL DEPENDENCY: " + global_dependencies
