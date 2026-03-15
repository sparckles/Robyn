from typing import Optional

from robyn import Request, SubRouter
from robyn.authentication import AuthenticationHandler, BearerGetter, Identity


class AsyncAuthHandler(AuthenticationHandler):
    """Auth handler with async authenticate() for testing async ORM patterns."""

    async def authenticate(self, request: Request) -> Optional[Identity]:
        token = self.token_getter.get_token(request)
        if token is not None:
            self.token_getter.set_token(request, token)
        if token == "valid":
            return Identity(claims={"async_key": "async_value"})
        return None


async_auth_subrouter = SubRouter(__name__, prefix="/async_auth_sub")
async_auth_subrouter.configure_authentication(AsyncAuthHandler(token_getter=BearerGetter()))


@async_auth_subrouter.get("/protected", auth_required=True)
async def async_auth_protected(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"async_key": "async_value"}
    return "async_auth_protected"


inherited_auth_subrouter = SubRouter(__name__, prefix="/inherited_auth_sub")


@inherited_auth_subrouter.get("/protected", auth_required=True)
async def inherited_auth_protected(request: Request):
    assert request.identity is not None
    assert request.identity.claims == {"key": "value"}
    return "inherited_auth_protected"
