import json
from os import environ as env
from typing import Any

import requests
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from jose import jwt
from starlette.requests import Request
from starlette.responses import Response

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
async def login(request: Request):  # type: ignore
    auth0 = oauth.create_client("auth0")

    redir_uri = request.url_for("callback")

    return await auth0.authorize_redirect(
        redirect_uri=redir_uri,
        audience=env.get("AUTH0_AUDIENCE"),
        request=request,
    )


@router.get("/signin-auth0")
async def callback(request: Request):  # type: ignore
    auth0 = oauth.create_client("auth0")
    token = await auth0.authorize_access_token(request)

    response = RedirectResponse(url="/")
    save_access_token(response, token)

    return response


@router.get("/logout")
def logout(request: Request):  # type: ignore
    redir = f'https://miapeer.auth0.com/v2/logout?returnTo={request.url_for("home")}&client_id={env.get("AUTH0_CLIENT_ID")}'
    response = RedirectResponse(url=redir)

    delete_access_token(response)

    return response


class AuthError(Exception):
    def __init__(self, error: dict[str, str], status_code: int) -> None:
        self.error = error
        self.status_code = status_code


def save_access_token(response: Response, token: Any) -> None:
    response.set_cookie("user", json.dumps(token), httponly=True)


def load_access_token(request: Request) -> Any:
    return json.loads(request.cookies.get("user", "{}"))


def delete_access_token(response: Response) -> None:
    response.delete_cookie("user")


def get_token_auth_header(request: Request) -> str:
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

    parts: list[str] = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with" " Bearer",
            },
            401,
        )
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
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


def verify_token(token: str) -> bool:
    jsonurl = requests.get(f"https://{env.get('AUTH0_DOMAIN')}/.well-known/jwks.json")
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
                algorithms=["RS256"],
                audience=env.get("AUTH0_AUDIENCE"),
                issuer=f"https://{env.get('AUTH0_DOMAIN')}/",
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError(
                {
                    "code": "invalid_claims",
                    "description": "incorrect claims," "please check the audience and issuer",
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

        # _request_ctx_stack.top.current_user = payload
        return True

    raise AuthError(
        {"code": "invalid_header", "description": "Unable to find appropriate key"},
        401,
    )


def requires_auth(request: Request) -> bool:
    """Determines if the Access Token is valid"""

    token = get_token_auth_header(request)

    return verify_token(token)


def has_scope(token: Any, required_scope: str) -> bool:
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("permissions"):
        token_scopes = unverified_claims["permissions"]
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False


def requires_scope(request: Request, required_scope: str) -> bool:
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header(request)

    return has_scope(token, required_scope)
