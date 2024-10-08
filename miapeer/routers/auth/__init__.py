from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlmodel import Session, select

from miapeer.auth.jwt import encode_jwt
from miapeer.dependencies import get_db, get_jwk
from miapeer.models.miapeer import Token, User

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

    # if not pw_verified:
    #     print(f"\n{get_password_hash(plain_password) = }\n")

    return pw_verified


def get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)  # pragma: no cover


def _authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.exec(select(User).where(User.email == username)).one_or_none()

    if user is None:
        return None

    if not _verify_password(password, user.password):
        return None

    return user


# TODO: Does data need to be sent encrypted, or is HTTPS sufficient?
# TODO: If something does need to be changed, difference between SSL and TLS?
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), jwk: str = Depends(get_jwk), db: Session = Depends(get_db)
) -> Token:
    user = _authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ACCESS_TOKEN_EXPIRE_MINUTES = 300  # TODO

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = encode_jwt(jwt_key=jwk, data={"sub": user.email, "exp": 0}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")
