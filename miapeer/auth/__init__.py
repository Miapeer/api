from pwdlib import PasswordHash
from fastapi import HTTPException

from sqlmodel import Session, select

from miapeer.models.miapeer import User
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

DEFAULT_JWT_ALGORITHM = "HS256"

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)

DUMMY_HASH = password_hash.hash("dummypassword")


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


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.exec(select(User).where(User.email == username)).one_or_none()

    if not user:
        # Perform a dummy verification to mitigate timing attacks
        _verify_password(plain_password=password, hashed_password=DUMMY_HASH)
        return None

    if not _verify_password(plain_password=password, hashed_password=user.password):
        return None

    return user
