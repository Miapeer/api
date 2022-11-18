import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.requests import Request

from miapeer.adapter.database import engine
from miapeer.dependencies import (
    get_current_active_user,
    is_authorized,
    is_miapeer_user,
)
from miapeer.models.user import User

router = APIRouter(
    tags=["Miapeer"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> str:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    \f
    :param item: User input.
    """

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


@router.get("/private", include_in_schema=True, dependencies=[Depends(is_miapeer_user)])
# def private(response: Response, token: str = Depends(token_auth_scheme)):
def private(current_user: User = Depends(get_current_active_user)) -> str:
    # """A valid access token is required to access this route"""

    # result = VerifyToken(token.credentials).verify()

    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result

    # return result
    from miapeer.dependencies import zzz

    return f"PRIVATE: {current_user}"
