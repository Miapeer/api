from datetime import datetime, timedelta
from enum import Enum
from os import environ as env
from typing import Optional

from jose import jwt
from jose.exceptions import JWKError, JWTError

DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30


class JwtException(Exception):
    ...


class JwtErrorMessage(str, Enum):
    INVALID_TOKEN = "Invalid token"
    INVALID_JWK = "Invalid JWT key"


def encode_jwt(jwt_key: str, data: dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    if jwt_key == "":
        raise JwtException(JwtErrorMessage.INVALID_JWK.value)

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode = data | {"exp": expire}

    encoded_jwt: str = jwt.encode(to_encode, jwt_key, algorithm=env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM))

    return encoded_jwt


def decode_jwt(jwt_key: str, token: str) -> dict[str, str]:
    if jwt_key == "":
        raise JwtException(JwtErrorMessage.INVALID_JWK.value)

    try:
        payload: dict[str, str] = jwt.decode(
            token, jwt_key, algorithms=[env.get("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)]
        )
    except JWTError:
        raise JwtException(JwtErrorMessage.INVALID_TOKEN.value)
    except JWKError:
        raise JwtException(JwtErrorMessage.INVALID_JWK.value)

    return payload
