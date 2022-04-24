import json
from functools import wraps
from os import environ as env

import requests
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from flask import _request_ctx_stack, request
from jose import jwt
from starlette.requests import Request

AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
API_AUDIENCE = env.get("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

router = APIRouter()

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


@router.get("/login")
async def login(request: Request):
    auth0 = oauth.create_client("auth0")

    redir_uri = request.url_for("callback")
    print(redir_uri)

    return await auth0.authorize_redirect(
        redirect_uri=redir_uri,
        audience=env.get("AUTH0_AUDIENCE"),
        request=request,
    )


@router.get("/signin-auth0")
async def callback(request: Request):
    print("callback")
    auth0 = oauth.create_client("auth0")
    token = await auth0.authorize_access_token(request)

    # token_permissions = token.get("permissions")

    response = RedirectResponse(url="/")
    response.set_cookie("user", json.dumps(token), httponly=True)

    return response


@router.get("/logout")
def logout(request: Request):
    print("logout: ")

    redir = f'https://miapeer.auth0.com/v2/logout?returnTo={request.url_for("home")}&client_id={env.get("AUTH0_CLIENT_ID")}'
    response = RedirectResponse(url=redir)

    request.session.clear()
    response.delete_cookie("user")

    return response


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Format error response and append status code
def get_token_auth_header() -> str:
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected",
            },
            401,
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with" " Bearer",
            },
            401,
        )
    elif len(parts) == 1:
        raise AuthError(
            {"code": "invalid_header", "description": "Token not found"}, 401
        )
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be" " Bearer token",
            },
            401,
        )

    token = parts[1]
    return token


def requires_auth(f):
    """Determines if the Access Token is valid"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()

        jsonurl = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        jwks = jsonurl.json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/",
                )
            except jwt.ExpiredSignatureError:
                raise AuthError(
                    {"code": "token_expired", "description": "token is expired"}, 401
                )
            except jwt.JWTClaimsError:
                raise AuthError(
                    {
                        "code": "invalid_claims",
                        "description": "incorrect claims,"
                        "please check the audience and issuer",
                    },
                    401,
                )
            except Exception:
                raise AuthError(
                    {
                        "code": "invalid_header",
                        "description": "Unable to parse authentication" " token.",
                    },
                    401,
                )

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError(
            {"code": "invalid_header", "description": "Unable to find appropriate key"},
            401,
        )

    return decorated


def requires_scope(required_scope: str) -> bool:
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("permissions"):
        token_scopes = unverified_claims["permissions"]
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False


class VerifyToken:
    """Does all the token verification using PyJWT"""

    def __init__(self, token):
        self.token = token
        # self.config = set_up()

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    def verify(self):
        # This gets the 'kid' from the passed token
        try:
            self.signing_key = self.jwks_client.get_signing_key_from_jwt(self.token).key
        except jwt.exceptions.PyJWKClientError as error:
            return {"status": "error", "msg": error.__str__()}
        except jwt.exceptions.DecodeError as error:
            return {"status": "error", "msg": error.__str__()}

        try:
            payload = jwt.decode(
                self.token,
                self.signing_key,
                algorithms=self.config["ALGORITHMS"],
                audience=self.config["API_AUDIENCE"],
                issuer=self.config["ISSUER"],
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return payload
