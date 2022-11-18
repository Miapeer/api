import json
from typing import Any, Iterator

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from requests import JSONDecodeError
from sqlmodel import Field, Session, SQLModel, create_engine, select

from miapeer.adapter.database import engine
from miapeer.auth import auth0, fastapi
from miapeer.models.application import Application
from miapeer.models.application_role import ApplicationRole
from miapeer.models.permission import Permission
from miapeer.models.role import Role
from miapeer.models.user import User

zzz = set()


oauth2_scheme = fastapi.oath2_bearer_scheme


async def get_current_active_user(
    current_user: User = Depends(fastapi.get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def get_access_token(user: str) -> Any:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token = json.loads(user).get("access_token")
    except JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    return token


def get_user_email(user: str) -> Any:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token = json.loads(user).get("userinfo", {}).get("email", None)
    except JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    return token


def get_user_roles(user: str) -> Any:
    email = get_user_email(user)

    return []


async def is_authorized(user: str = Cookie(None)) -> None:
    print(f"\n{user = }\n")  # TODO: Remove this!!!
    token = get_access_token(user)

    try:
        auth0.verify_token(token)
    except auth0.AuthError as ex:
        raise HTTPException(status_code=401, detail=ex.error)
    except Exception:
        raise HTTPException(status_code=401, detail="Error decoding access token")


async def has_permission(email: str, application: str, role: str) -> bool:
    # TODO: https://sqlmodel.tiangolo.com/tutorial/fastapi/relationships/
    with next(get_session()) as session:
        sql = (
            select(User.email, Application.name, Role.name)
            .join(Permission)
            .join(ApplicationRole)
            .join(Application)
            .join(Role)
            .where(User.email == email)
        )
        users = session.exec(sql)
        for u in users:
            print(f"\n{u = }\n")  # TODO: Remove this!!!
            zzz.add(f"{u[0]}-{u[1]}-{u[2]}")

    # TODO: Add memoization
    # TODO: Add expiration

    return f"{email}-{application}-{role}" in zzz


async def is_miapeer_user(user: str = Cookie(None)) -> None:
    email = get_user_email(user)
    print(f"\n{email = }\n")  # TODO: Remove this!!!
    # if not auth0.has_scope(token,  "write:zomething"):
    if not await has_permission(email, "Miapeer", "User"):
        raise HTTPException(status_code=403, detail="Forbidden")
