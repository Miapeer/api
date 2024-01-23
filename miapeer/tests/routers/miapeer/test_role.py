from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import Role, RoleCreate, RoleUpdate
from miapeer.routers.miapeer import role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def role_id() -> int:
    return 12345


@pytest.fixture
def role_name() -> str:
    return "some role"


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestGetAll:
    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_role.name, miapeer_role.role_id \nFROM miapeer_role"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await role.get_all_roles(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def role_create(self, role_name: str) -> RoleCreate:
        return RoleCreate(name=role_name)

    @pytest.fixture
    def role_to_add(self, role_name: str) -> Role:
        return Role(role_id=None, name=role_name, password="", disabled=False)

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        role_create: RoleCreate,
        role_to_add: Role,
        mock_db: Mock,
    ) -> None:
        await role.create_role(role=role_create, db=mock_db)

        mock_db.add.assert_called_once_with(role_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(role_to_add)
        # Don't need to test the response here because it's just the updated role_to_add


class TestGet:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_get_with_data(self, role_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await role.get_role(role_id=role_id, db=mock_db)

        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, role_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await role.get_role(role_id=role_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_role_found(self, role_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await role.delete_role(role_id=role_id, db=mock_db)

        mock_db.delete.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_delete_with_role_not_found(self, role_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await role.delete_role(role_id=role_id, db=mock_db)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def role_to_update(self, role_name: str, portfolio_id: int) -> Role:
        return Role(role_id=None, name=role_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def updated_role(self) -> RoleUpdate:
        return RoleUpdate(name="some new name")

    @pytest.mark.parametrize("db_get_return_val", [role_to_update])
    async def test_update_with_role_found(
        self,
        role_id: int,
        updated_role: RoleUpdate,
        mock_db: Mock,
        db_get_return_val: Role,
    ) -> None:
        response = await role.update_role(
            role_id=role_id,
            role=updated_role,
            db=mock_db,
        )

        mock_db.add.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_get_return_val)
        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_role_not_found(
        self,
        role_id: int,
        updated_role: RoleUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await role.update_role(
                role_id=role_id,
                role=updated_role,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
