from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import Permission, PermissionCreate, PermissionRead
from miapeer.routers.miapeer import permission

pytestmark = pytest.mark.asyncio


raw_permission_id = 12345


@pytest.fixture
def permission_id() -> int:
    return raw_permission_id


@pytest.fixture
def application_role_id() -> int:
    return 321


@pytest.fixture
def basic_permission(user_id: int, application_role_id: int) -> Permission:
    return Permission(permission_id=None, user_id=user_id, application_role_id=application_role_id)


@pytest.fixture
def complete_permission(permission_id: int, basic_permission: Permission) -> Permission:
    return Permission.model_validate(basic_permission.model_dump(), update={"permission_id": permission_id})


class TestGetAll:
    @pytest.fixture
    def multiple_permissions(self, complete_permission: Permission) -> list[Permission]:
        return [complete_permission, complete_permission]

    @pytest.fixture
    def expected_multiple_permissions(self, complete_permission: Permission) -> list[PermissionRead]:
        working_permission = PermissionRead.model_validate(complete_permission)
        return [working_permission, working_permission]

    @pytest.fixture
    def expected_sql(self) -> str:
        return (
            f"SELECT miapeer_permission.user_id, miapeer_permission.application_role_id, miapeer_permission.permission_id \nFROM miapeer_permission"
        )

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (pytest.lazy_fixture("multiple_permissions"), pytest.lazy_fixture("expected_multiple_permissions"))],
    )
    async def test_get_all(self, mock_db: Mock, expected_sql: str, expected_response: list[PermissionRead]) -> None:
        response = await permission.get_all_permissions(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.permission_id = raw_permission_id

    @pytest.fixture
    def permission_to_create(self, user_id: int, application_role_id: int) -> PermissionCreate:
        return PermissionCreate(user_id=user_id, application_role_id=application_role_id)

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        permission_to_create: PermissionCreate,
        complete_permission: Permission,
        mock_db: Mock,
    ) -> None:
        await permission.create_permission(permission=permission_to_create, db=mock_db)

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_permission.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_permission.model_dump()

        # Don't need to test the response here because it's just the updated permission_to_add


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_permission: Permission) -> PermissionRead:
        return PermissionRead.model_validate(complete_permission)

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_permission")])
    async def test_get_with_data(self, permission_id: int, mock_db: Mock, expected_response: PermissionRead) -> None:
        response = await permission.get_permission(permission_id=permission_id, db=mock_db)

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, permission_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await permission.get_permission(permission_id=permission_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_permission_found(self, permission_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await permission.delete_permission(permission_id=permission_id, db=mock_db)

        mock_db.delete.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_delete_with_permission_not_found(self, permission_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await permission.delete_permission(permission_id=permission_id, db=mock_db)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
