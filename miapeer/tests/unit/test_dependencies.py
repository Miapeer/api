from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from miapeer import dependencies
from miapeer.models.miapeer import User


class TestGetJwk:
    @patch(f"{dependencies.__name__}.env")
    @pytest.mark.parametrize("get_env_var", ["something", None])
    def test_get_jwk(self, patched_env: Mock, get_env_var: Any) -> None:
        patched_env.get.return_value = get_env_var
        return_val = dependencies.get_jwk()
        assert return_val == get_env_var


@pytest.mark.asyncio
class TestGetCurrentUser:
    @pytest.mark.parametrize("db_first_return_val", ["some data", 123])
    async def test_get_current_user(self, mock_db: Mock, valid_jwt: str, jwk: str, db_first_return_val: Any) -> None:
        res = await dependencies.get_current_user(token=valid_jwt, jwt_key=jwk, db=mock_db)
        assert res == db_first_return_val

    async def test_get_current_user_raises_exception_when_username_not_provided(self, mock_db: Mock, jwt_missing_sub: str, jwk: str) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_user(token=jwt_missing_sub, jwt_key=jwk, db=mock_db)

    @pytest.mark.parametrize("db_first_return_val", [None])
    async def test_get_current_user_raises_exception_when_user_not_found(self, mock_db: Mock, valid_jwt: str, jwk: str) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_user(token=valid_jwt, jwt_key=jwk, db=mock_db)


@pytest.mark.asyncio
class TestGetCurrentActiveUser:
    async def test_returns_user(self, user: User) -> None:
        returned_user = await dependencies.get_current_active_user(current_user=user)
        assert returned_user == user

    async def test_inactive_user_raises_exception(self, inactive_user: User) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_active_user(current_user=inactive_user)


class TestHasPermission:
    @pytest.mark.parametrize("db_all_return_val", [[{}]])
    def test_has_permission(self, mock_db: Mock) -> None:
        permitted = dependencies.has_permission(db=mock_db, email="", application=dependencies.Applications.MIAPEER, role=dependencies.Roles.USER)
        assert permitted is True

    @pytest.mark.parametrize("db_all_return_val", [[]])
    def test_no_permission(self, mock_db: Mock) -> None:
        permitted = dependencies.has_permission(db=mock_db, email="", application=dependencies.Applications.MIAPEER, role=dependencies.Roles.USER)
        assert permitted is False


class TestIndividualPermissions:
    @patch(f"{dependencies.__name__}.has_permission")
    @pytest.mark.parametrize(
        "permission_function",
        [
            dependencies.is_miapeer_user,
            dependencies.is_miapeer_admin,
            dependencies.is_miapeer_super_user,
            dependencies.is_quantum_user,
            dependencies.is_quantum_admin,
            dependencies.is_quantum_super_user,
        ],
    )
    def test_has_permission(
        self,
        patched_has_permission: Mock,
        mock_db: Mock,
        permission_function: Any,
        user: User,
    ) -> None:
        patched_has_permission.return_value = True

        permission_function(db=mock_db, user=user)

    @patch(f"{dependencies.__name__}.has_permission")
    @pytest.mark.parametrize(
        "permission_function",
        [
            dependencies.is_miapeer_user,
            dependencies.is_miapeer_admin,
            dependencies.is_miapeer_super_user,
            dependencies.is_quantum_user,
            dependencies.is_quantum_admin,
            dependencies.is_quantum_super_user,
        ],
    )
    def test_no_permission(
        self,
        patched_has_permission: Mock,
        mock_db: Mock,
        permission_function: Any,
        user: User,
    ) -> None:
        patched_has_permission.return_value = False

        with pytest.raises(HTTPException):
            permission_function(db=mock_db, user=user)
