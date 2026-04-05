from datetime import datetime, timedelta, timezone
from enum import Enum
from os import environ as env
from typing import Optional
from fastapi import HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
from typing_extensions import TypedDict

DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

TokenData = TypedDict("TokenData", {"sub": str, "exp": Optional[int]})


class JwtException(Exception): ...


class JwtErrorMessage(str, Enum):
    INVALID_TOKEN = "Invalid token"
    INVALID_JWK = "Invalid JWT key"


def get_jwk() -> Optional[str]:
    return env.get("JWT_SECRET_KEY")


def encode_jwt(
    data: dict[str, str | int | None], expires_delta: Optional[timedelta] = None
) -> str:
    jwt_key = get_jwk()
    algorithm = env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)

    if not jwt_key:
        raise JwtException(JwtErrorMessage.INVALID_JWK.value)

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif "exp" in data and data.get("exp") is not None:
        token_exp = data.get("exp")
        assert isinstance(token_exp, int)
        expire = datetime.fromtimestamp(token_exp)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})  # ty: ignore [no-matching-overload]

    encoded_jwt = jwt.encode(to_encode, jwt_key, algorithm=algorithm)

    return encoded_jwt


def decode_jwt(token: str) -> TokenData:
    jwt_key = get_jwk()

    if not jwt_key:
        raise JwtException(JwtErrorMessage.INVALID_JWK.value)

    try:
        payload = jwt.decode(
            jwt=token,
            key=jwt_key,
            algorithms=env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM),
        )
        username = payload.get("sub")
        expiration = payload.get("exp")

        if not username or not expiration:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is incomplete",
                headers={"WWW-Authenticate": "Bearer"},
            )

        typed_payload: TokenData = {
            "sub": username,
            "exp": expiration,
        }

        if datetime.fromtimestamp(expiration, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise InvalidTokenError("Token has expired")

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return typed_payload
