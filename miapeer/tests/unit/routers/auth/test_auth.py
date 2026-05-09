from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from miapeer.models.miapeer import User
from miapeer.routers import auth

pytestmark = pytest.mark.asyncio


class TestLoginForAccessToken:
    @pytest.fixture
    def form_data(self, user_password: str) -> OAuth2PasswordRequestForm:
        return OAuth2PasswordRequestForm(
            username="aaa", password=user_password, scope=""
        )

    @pytest.fixture
    def user_with_incorrect_password(self, user: User) -> User:
        user.password = "$2b$12$wqFnN2q.I.Y3LU5K32u5iORvMH3Zx2C6Lm84m.KSJG3IqKjLsHQb6"
        return user

    @patch(f"{auth.__name__}.authenticate_user")
    @patch(f"{auth.__name__}.jwt.encode_jwt", return_value="a token")
    async def test_succeeds(
        self,
        mock_encode_jwt: Mock,
        mock_authenticate_user: Mock,
        form_data: OAuth2PasswordRequestForm,
        mock_db: Mock,
        user: User,
    ) -> None:
        mock_authenticate_user.return_value = user

        response = await auth.login_for_access_token(form_data=form_data, db=mock_db)

        assert response.token_type == "bearer"
        assert response.access_token == "a token"

    @patch(f"{auth.__name__}.authenticate_user", return_value=None)
    async def test_raises_exception_when_user_not_found(
        self,
        form_data: OAuth2PasswordRequestForm,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await auth.login_for_access_token(form_data=form_data, db=mock_db)
