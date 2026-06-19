from robyn import Request, SubRouter
from robyn.authentication import AuthenticationHandler, BearerGetter, Identity


class AsyncAuthHandler(AuthenticationHandler):
    """An authentication handler with an async authenticate() — exercises the
    async path used by async ORMs / HTTP clients (#1157, #1296)."""

    async def authenticate(self, request: Request) -> Identity | None:
        token = self.token_getter.get_token(request)
        if token == "valid":
            return Identity(claims={"async_key": "async_value"})
        return None


# A SubRouter that configures its OWN async handler.
async_auth_subrouter = SubRouter(prefix="/async_auth_sub")
async_auth_subrouter.configure_authentication(AsyncAuthHandler(token_getter=BearerGetter()))


@async_auth_subrouter.get("/protected", auth_required=True)
async def async_auth_protected(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"async_key": "async_value"}
    return "async_auth_protected"


# A SubRouter with NO handler of its own — it inherits the app's handler (#1026).
inherited_auth_subrouter = SubRouter(prefix="/inherited_auth_sub")


@inherited_auth_subrouter.get("/protected", auth_required=True)
async def inherited_auth_protected(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "inherited_auth_protected"
