from datetime import datetime, timedelta
from os import environ as env
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from miapeer.auth.abstract import AbstractAuthenticator
from miapeer.dependencies import get_db
from miapeer.models.auth import Token
from miapeer.models.user import User

DEFAULT_JWT_ALGORITHM = "HS256"

# TODO: Need salt?   https://auth0.com/blog/hashing-in-action-understanding-bcrypt/
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/miapeer/v1/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_verified = _pwd_context.verify(
        plain_password,
        hashed_password,
    )

    if not pw_verified:
        print(f"\n{_get_password_hash(plain_password) = }\n")

    return pw_verified


def _get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


def _authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.exec(select(User).where(User.email == username)).one_or_none()
    if user is None:
        return None
    if not _verify_password(password, user.password):
        return None
    return user


def _create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})  # type: ignore

    encoded_jwt: str = jwt.encode(
        to_encode, env.get("JWT_SECRET_KEY"), algorithm=env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)
    )

    return encoded_jwt


# TODO: Does data need to be sent encrypted, or is HTTPS sufficient?
# TODO: If something does need to be changed, difference between SSL and TLS?
@router.post("/token", response_model=Token)
async def _login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> dict[str, str]:
    user = _authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # TODO

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = _create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}
