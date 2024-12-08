from robyn import Request, SubRouter

auth_subrouter_endpoint = SubRouter(__file__, "/auth_subrouter_endpoint")


@auth_subrouter_endpoint.get("/auth_subroute_sync", auth_required=True)
def sync_subrouter_auth_endpoint(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_endpoint.get("/auth_subroute_async", auth_required=True)
async def async_subrouter_auth_endpoint(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


auth_subrouter_include = SubRouter(__file__, "/auth_subrouter_include")


@auth_subrouter_include.get("/auth_subroute_sync")
def sync_subrouter_auth_include(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include.get("/auth_subroute_async")
async def async_subrouter_auth_include(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include.get("/noauth_subroute_sync", auth_required=False)
def sync_subrouter_noauth_include(request: Request):
    return "bypassed"


@auth_subrouter_include.get("/noauth_subroute_async", auth_required=False)
async def async_subrouter_noauth_include(request: Request):
    return "bypassed"


auth_subrouter_instance = SubRouter(__file__, "/auth_subrouter_instance", auth_required=True)


@auth_subrouter_instance.get("/auth_subroute_sync")
def sync_subrouter_auth_instance(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_instance.get("/auth_subroute_async")
async def async_subrouter_auth_instance(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_instance.get("/noauth_subroute_sync", auth_required=False)
def sync_subrouter_noauth_instance(request: Request):
    return "bypassed"


@auth_subrouter_instance.get("/noauth_subroute_async", auth_required=False)
async def async_subrouter_noauth_instance(request: Request):
    return "bypassed"


auth_subrouter_include_false = SubRouter(__file__, "/auth_subrouter_include_false", auth_required=True)


@auth_subrouter_include_false.get("/auth_subroute_sync", auth_required=True)
def sync_subrouter_auth_include_false(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include_false.get("/auth_subroute_async", auth_required=True)
async def async_subrouter_auth_include_false(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include_false.get("/noauth_subroute_sync")
def sync_subrouter_noauth_include_false(request: Request):
    return "bypassed"


@auth_subrouter_include_false.get("/noauth_subroute_async")
async def async_subrouter_noauth_include_false(request: Request):
    return "bypassed"


auth_subrouter_include_true = SubRouter(__file__, "/auth_subrouter_include_true", auth_required=False)


@auth_subrouter_include_true.get("/auth_subroute_sync")
def sync_subrouter_auth_include_true(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include_true.get("/auth_subroute_async")
async def async_subrouter_auth_include_true(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "authenticated"


@auth_subrouter_include_true.get("/noauth_subroute_sync", auth_required=False)
def sync_subrouter_noauth_include_true(request: Request):
    return "bypassed"


@auth_subrouter_include_true.get("/noauth_subroute_async", auth_required=False)
async def async_subrouter_noauth_include_true(request: Request):
    return "bypassed"
