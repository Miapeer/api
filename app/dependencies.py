import json

from fastapi import Cookie, HTTPException
from requests import JSONDecodeError

from app.auth import auth0


async def get_access_token(user: str):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token = json.loads(user).get("access_token")
    except JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    return token


async def is_authorized(user: str = Cookie(None)):
    token = await get_access_token(user)

    try:
        auth0.verify_token(token)
    except auth0.AuthError as ex:
        raise HTTPException(status_code=401, detail=ex.error)
    except Exception:
        raise HTTPException(status_code=401, detail="Error decoding access token")


async def is_zomething(user: str = Cookie(None)):
    token = await get_access_token(user)

    if not auth0.has_scope(token, "write:zomething"):
        raise HTTPException(status_code=403, detail="Forbidden")
