import json
from os import environ as env
from typing import Any, Iterator

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from requests import JSONDecodeError
from sqlmodel import Field, Session, select

from miapeer.adapter.database import engine
from miapeer.models.application import Application
from miapeer.models.application_role import ApplicationRole
from miapeer.models.auth import Token, TokenData
from miapeer.models.permission import Permission
from miapeer.models.role import Role
from miapeer.models.user import User

fake_users_db = {
    "johndoe@example.com": {
        "username": "johndoe@example.com",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

# TODO: to get a string like this run:
# openssl rand -hex 32
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

zzz = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/miapeer/v1/auth/token")

# TODO: Make async? ...or already async?
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, env.get("JWT_SECRET_KEY"), algorithms=[env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)]
        )
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # def get_user(username: str) -> Optional[User]:
    #     if username in db:
    #         user_dict = db[username]
    #         return User(**user_dict)

    #     return None

    #     user = get_user(fake_users_db, username=token_data.username)
    user = session.exec(select(User).where(User.email == token_data.username)).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


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


# async def is_authorized(user: str = Cookie(None)) -> None:
#     print(f"\n{user = }\n")  # TODO: Remove this!!!
#     token = get_access_token(user)

#     try:
#         auth0.verify_token(token)
#     except auth0.AuthError as ex:
#         raise HTTPException(status_code=401, detail=ex.error)
#     except Exception:
#         raise HTTPException(status_code=401, detail="Error decoding access token")


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
