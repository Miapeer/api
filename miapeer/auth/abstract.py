from abc import ABC

from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer

from miapeer.models.miapeer import User


# Not in use
class AbstractAuthenticator(ABC):
    def get_router(self) -> APIRouter:
        raise NotImplementedError

    def get_oauth2_scheme(self) -> OAuth2PasswordBearer:
        raise NotImplementedError

    async def get_current_user(self, token: str) -> User:
        raise NotImplementedError
