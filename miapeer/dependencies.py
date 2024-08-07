from enum import Enum
from os import environ as env
from typing import Annotated, Iterator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from miapeer.adapter.database import engine
from miapeer.auth.jwt import decode_jwt
from miapeer.models.miapeer import (
    Application,
    ApplicationRole,
    Permission,
    Role,
    TokenData,
    User,
)

DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Applications(str, Enum):
    MIAPEER = "Miapeer"
    QUANTUM = "Quantum"


class Roles(str, Enum):
    USER = "User"
    ADMIN = "Administrator"
    SUPER_USER = "Super User"


permission_cache: set[str] = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/miapeer/v1/auth/token")


def get_db() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def get_jwk() -> Optional[str]:
    return env.get("JWT_SECRET_KEY")


# TODO: Cache results to prevent multiple DB lookups
async def get_current_user(
    token: str = Depends(oauth2_scheme), jwt_key: str = Depends(get_jwk), db: Session = Depends(get_db)
) -> User:
    payload = decode_jwt(token=token, jwt_key=jwt_key)

    username: Optional[str] = payload.get("sub")

    if username is None or username == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = TokenData(username=username)

    user = db.exec(select(User).where(User.email == token_data.username)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # print(f"\n{permission_cache = }\n")  # TODO: Remove this!!!

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


# async def is_authorized(user: str = Cookie(None)) -> None:
#     print(f"\n{user = }\n")  # TODO: Remove this!!!
#     token = get_access_token(user)

#     try:
#         auth0.verify_token(token)
#     except auth0.AuthError as ex:
#         raise HTTPException(status_code=401, detail=ex.error)
#     except Exception:
#         raise HTTPException(status_code=401, detail="Error decoding access token")


def has_permission(db: Session, email: str, application: Applications, role: Roles) -> bool:
    print("has_permission")
    # TODO: https://sqlmodel.tiangolo.com/tutorial/fastapi/relationships/

    # # Check the cache first
    # if f"{email}-{application}-{role}" in permission_cache:
    #     return True

    sql = (
        select(User.email, Application.name, Role.name)
        .join(Permission)
        .join(ApplicationRole)
        .join(Application)
        .join(Role)
        .where(User.email == email)
        .where(Role.name == role)
        .where(Application.name == application)
    )
    users = db.exec(sql).all()

    # print(f'\n{users = }\n') # TODO: Remove this!!!

    # for u in users:
    #     permission_cache.add(f"{u[0]}-{u[1]}-{u[2]}")

    # print(f'\n{permission_cache = }\n') # TODO: Remove this!!!

    # TODO: Improve memoization
    # TODO: Add expiration

    # return f"{email}-{application}-{role}" in permission_cache

    return len(users) > 0


def is_miapeer_user(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.MIAPEER, Roles.USER):
        raise HTTPException(status_code=400, detail="Unauthorized: is_miapeer_user")


def is_miapeer_admin(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.MIAPEER, Roles.ADMIN):
        raise HTTPException(status_code=400, detail="Unauthorized: is_miapeer_admin")


def is_miapeer_super_user(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.MIAPEER, Roles.SUPER_USER):
        raise HTTPException(status_code=400, detail="Unauthorized: is_miapeer_super_user")


# Dependencies are "and"s not "or"s. Need a separate function for each combo
# ...or...
# TODO: https://fastapi.tiangolo.com/advanced/advanced-dependencies/


def is_quantum_user(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.QUANTUM, Roles.USER):
        raise HTTPException(status_code=400, detail="Unauthorized: is_quantum_user")


def is_quantum_admin(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.QUANTUM, Roles.ADMIN):
        raise HTTPException(status_code=400, detail="Unauthorized: is_quantum_admin")


def is_quantum_super_user(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    if not has_permission(db, user.email, Applications.QUANTUM, Roles.SUPER_USER):
        raise HTTPException(status_code=400, detail="Unauthorized: is_quantum_super_user")
