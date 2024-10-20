from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from miapeer.models.miapeer import User
from miapeer.routers import auth

pytestmark = pytest.mark.asyncio


@pytest.fixture
def form_data(user_password: str) -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(username="aaa", password=user_password, scope="")


@pytest.fixture
def user_with_incorrect_password(user: User) -> User:
    user.password = "$2b$12$wqFnN2q.I.Y3LU5K32u5iORvMH3Zx2C6Lm84m.KSJG3IqKjLsHQb6"
    return user


@pytest.mark.parametrize("db_one_or_none_return_val", [pytest.lazy_fixture("user")])
async def test_access_token(form_data: OAuth2PasswordRequestForm, mock_db: Mock) -> None:
    response = await auth.login_for_access_token(form_data=form_data, jwk="My secret key", db=mock_db)

    assert response.token_type == "bearer"
    assert len(response.access_token) > 0


@pytest.mark.parametrize("db_one_or_none_return_val", [None])
async def test_access_token_when_user_not_found(form_data: OAuth2PasswordRequestForm, mock_db: Mock) -> None:
    with pytest.raises(HTTPException):
        await auth.login_for_access_token(form_data=form_data, jwk="My secret key", db=mock_db)


@pytest.mark.parametrize("db_one_or_none_return_val", [pytest.lazy_fixture("user_with_incorrect_password")])
async def test_access_token_when_password_incorrect(form_data: OAuth2PasswordRequestForm, mock_db: Mock) -> None:
    with pytest.raises(HTTPException):
        await auth.login_for_access_token(form_data=form_data, jwk="My secret key", db=mock_db)
