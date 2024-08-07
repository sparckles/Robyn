from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from base64 import b64decode

from robyn.robyn import Headers, Identity, Request, Response
from robyn.status_codes import HTTP_401_UNAUTHORIZED


class AuthenticationNotConfiguredError(Exception):
    """
    This exception is raised when the authentication is not configured.
    """

    def __str__(self):
        return "Authentication is not configured. Use app.configure_authentication() to configure it."


class TokenGetter(ABC):
    @property
    def scheme(self) -> str:
        """
        Gets the scheme of the token.
        :return: The scheme of the token.
        """
        return self.__class__.__name__

    @classmethod
    @abstractmethod
    def get_token(cls, request: Request) -> Optional[str]:
        """
        Gets the token from the request.
        This method should not decode the token. Decoding is the role of the authentication handler.
        :param request: The request object.
        :return: The encoded token.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def set_token(cls, request: Request, token: str):
        """
        Sets the token in the request.
        This method should not encode the token. Encoding is the role of the authentication handler.
        :param request: The request object.
        :param token: The encoded token.
        """
        raise NotImplementedError()

    @classmethod
    def get_credentials(cls, request: Request):
        """
        Only available for Basic Getter.
        Gets credentials from the request token basic.
        This method will decode the token and return username password
        :param request: The request object.
        :return: Tuple of username and password.
        """
        pass


class AuthenticationHandler(ABC):
    def __init__(self, token_getter: TokenGetter, name: str, default: bool = False):
        """
        Creates a new instance of the AuthenticationHandler class.
        This class is an abstract class used to authenticate a user.
        :param token_getter: The token getter used to get the token from the request.
        :param name: The name of authentication handler ex: jwt, basic, etc.
        :param default: set authentication handler is the default handler.
        """
        self.token_getter = token_getter
        self.name = name
        self.default = default

    @property
    def unauthorized_response(self) -> Response:
        return Response(
            headers=Headers({"WWW-Authenticate": self.token_getter.scheme}),
            description="Unauthorized",
            status_code=HTTP_401_UNAUTHORIZED,
        )

    @abstractmethod
    def authenticate(self, request: Request) -> Optional[Identity]:
        """
        Authenticates the user.
        :param request: The request object.
        :return: The identity of the user.
        """
        raise NotImplementedError()


class BearerGetter(TokenGetter):
    """
    This class is used to get the token from the Authorization header.
    The scheme of the header must be Bearer.
    """

    @classmethod
    def get_token(cls, request: Request) -> Optional[str]:
        if "authorization" in request.headers:
            authorization_header = request.headers.get("authorization")
        else:
            authorization_header = None

        if not authorization_header or not authorization_header.startswith("Bearer "):
            return None

        return authorization_header[7:]  # Remove the "Bearer " prefix

    @classmethod
    def set_token(cls, request: Request, token: str):
        request.headers["Authorization"] = f"Bearer {token}"


class BasicGetter(TokenGetter):
    """
    This class is used to get the token from the Authorization header.
    The scheme of the header must be Basic.
    """

    @classmethod
    def get_token(cls, request: Request) -> Optional[str]:
        authorization_header = request.headers.get("authorization")
        if not authorization_header or not authorization_header.startswith("Basic "):
            return None

        return authorization_header[6:]  # Remove the "Basic " prefix

    @classmethod
    def set_token(cls, request: Request, token: str):
        request.headers["Authorization"] = f"Basic {token}"

    @classmethod
    def get_credentials(cls, request: Request) -> Union[Tuple[str, str], Tuple[None, None]]:
        basic_token = cls.get_token(request)
        try:
            basic_token_decoded = b64decode(basic_token).decode()
            username, _, password = basic_token_decoded.partition(":")
            return (username, password)  # Return username password from basic authorization
        except Exception:
            return (None, None)
