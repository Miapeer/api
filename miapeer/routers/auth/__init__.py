from datetime import timedelta
from typing import Optional
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlmodel import Session, select

from miapeer.auth.jwt import encode_jwt
from miapeer.dependencies import get_db
from miapeer.models.miapeer import Token, User

DEFAULT_JWT_ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

router = APIRouter(
    prefix="/miapeer/v1/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_verified = password_hash.verify(
        plain_password,
        hashed_password,
    )

    if not pw_verified:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return pw_verified


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)  # pragma: no cover


def _authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.exec(select(User).where(User.email == username)).one_or_none()

    if not user:
        # Perform a dummy verification to mitigate timing attacks
        _verify_password(password, DUMMY_HASH)
        return None

    if not _verify_password(password, user.password):
        return None

    return user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = _authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = encode_jwt(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
