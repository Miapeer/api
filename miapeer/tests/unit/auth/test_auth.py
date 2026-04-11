from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer import auth
from pytest_lazy_fixtures import lf as lazy_fixture


class TestVerifyPassword:
    @patch(f"{auth.__name__}.password_hash")
    def test_returns_true_when_password_is_correct(self, mock_password_hash: Mock):
        mock_password_hash.verify.return_value = True

        is_verified = auth._verify_password("aaa", "bbb")

        assert is_verified is True

    @patch(f"{auth.__name__}.password_hash")
    def test_raises_exception_when_password_is_incorrect(
        self, mock_password_hash: Mock
    ):
        mock_password_hash.verify.return_value = False

        is_verified = "initial value"
        with pytest.raises(HTTPException) as exp:
            is_verified = auth._verify_password("aaa", "bbb")

        assert exp.value.detail == "Incorrect username or password"
        assert is_verified == "initial value"  # Unchanged


class TestGetPasswordHash:
    @patch(f"{auth.__name__}.password_hash")
    def test_returns_hash(self, mock_password_hash: Mock):
        mock_password_hash.hash.return_value = "hashed pw"

        hashed_password = auth.get_password_hash("password")

        assert hashed_password == "hashed pw"


class TestAuthenticateUser:
    @patch(f"{auth.__name__}._verify_password", return_value=True)
    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("user")])
    def test_succeeds(
        self,
        mock_verify_password: Mock,
        user: User,
        mock_db: Mock,
        user_name: str,
        user_password: str,
        user_hashed_password: str,
    ):
        returned_user = auth.authenticate_user(
            db=mock_db, username=user_name, password=user_password
        )

        mock_verify_password.assert_called_once_with(
            plain_password=user_password, hashed_password=user_hashed_password
        )
        assert returned_user == user

    @patch(f"{auth.__name__}._verify_password")
    @patch(f"{auth.__name__}.DUMMY_HASH", return_value="dummy hash")
    @pytest.mark.parametrize("db_one_or_none_return_val", [None])
    def test_user_not_found(
        self,
        mock_dummy_hash: Mock,
        mock_verify_password: Mock,
        mock_db: Mock,
        user_name: str,
        user_password: str,
    ):
        returned_user = auth.authenticate_user(
            db=mock_db, username=user_name, password=user_password
        )

        mock_verify_password.assert_called_once_with(
            plain_password=user_password, hashed_password=mock_dummy_hash
        )
        assert returned_user is None

    @patch(f"{auth.__name__}._verify_password", return_value=False)
    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("user")])
    def test_password_incorrect(
        self,
        mock_verify_password: Mock,
        mock_db: Mock,
        user_name: str,
        user_password: str,
        user_hashed_password: str,
    ):
        returned_user = auth.authenticate_user(
            db=mock_db, username=user_name, password=user_password
        )

        mock_verify_password.assert_called_once_with(
            plain_password=user_password, hashed_password=user_hashed_password
        )
        assert returned_user is None
