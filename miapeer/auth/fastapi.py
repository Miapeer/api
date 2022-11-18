import json
from datetime import datetime, timedelta
from os import environ as env
from typing import Optional, Union

import requests
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from miapeer.models.user import User, UserInDb

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
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


router = APIRouter(
    prefix="/miapeer/v1/auth",
    tags=["Auth"],
    # dependencies=[Depends(is_authorized)],
    responses={404: {"description": "Not found"}},
)

# token_auth_scheme = HTTPBearer()
oath2_bearer_scheme = OAuth2PasswordBearer(tokenUrl="/miapeer/v1/auth/token")


def get_user(db: dict[str, dict[str, str]], username: str) -> Optional[UserInDb]:
    if username in db:
        user_dict = db[username]
        return UserInDb(**user_dict)

    return None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(fake_db: dict[str, dict[str, str]], username: str, password: str) -> Union[User | bool]:
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oath2_bearer_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"\n{token = }\n")  # TODO: Remove this!!!
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"\n{payload = }\n")  # TODO: Remove this!!!
        username: str = payload.get("sub")
        print(f"\n{username = }\n")  # TODO: Remove this!!!
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        print(f"\n{token_data = }\n")  # TODO: Remove this!!!
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def fake_hash_password(password: str) -> str:
    return "fakehashed" + password


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
