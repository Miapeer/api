import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.requests import Request

from miapeer.adapter.database import engine
from miapeer.dependencies import is_authorized, is_zomething

router = APIRouter(
    tags=["miapeer"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> str:
    access_token = json.loads(request.cookies.get("user", "{}"))

    return f"""
<html>
  <head>
    <meta charset="utf-8" />
    <title>Auth0 Example</title>
  </head>
  <body>
    <h1>Welcome {access_token.get('userinfo').get('email') if access_token else 'Guest'}</h1>
    <p>{'<a href="/logout">Logout</a>' if access_token else '<a href="/login">Login</a>'}</p>
    <p>{access_token}</p>
  </body>
</html>
    """


@router.get("/private", dependencies=[Depends(is_authorized), Depends(is_zomething)])
# def private(response: Response, token: str = Depends(token_auth_scheme)):
def private() -> str:
    # """A valid access token is required to access this route"""

    # result = VerifyToken(token.credentials).verify()

    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result

    # return result
    return "PRIVATE"
