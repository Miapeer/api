from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import (
    ApplicationRole,
    ApplicationRoleCreate,
    ApplicationRoleUpdate,
)
from miapeer.routers.miapeer import application_role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def application_role_id() -> int:
    return 12345


@pytest.fixture
def application_id() -> int:
    return 111


@pytest.fixture
def role_id() -> int:
    return 222


@pytest.fixture
def application_role_description() -> str:
    return "a_r desc"


class TestGetAll:
    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_application_role.application_id, miapeer_application_role.role_id, miapeer_application_role.description, miapeer_application_role.application_role_id \nFROM miapeer_application_role"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await application_role.get_all_application_roles(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def application_role_create(
        self, application_id: int, role_id: int, application_role_description: str
    ) -> ApplicationRoleCreate:
        return ApplicationRoleCreate(
            application_id=application_id, role_id=role_id, description=application_role_description
        )

    @pytest.fixture
    def application_role_to_add(
        self, application_id: int, role_id: int, application_role_description: str
    ) -> ApplicationRole:
        return ApplicationRole(
            application_role_id=None,
            application_id=application_id,
            role_id=role_id,
            description=application_role_description,
        )

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        application_role_create: ApplicationRoleCreate,
        application_role_to_add: ApplicationRole,
        mock_db: Mock,
    ) -> None:
        await application_role.create_application_role(application_role=application_role_create, db=mock_db)

        mock_db.add.assert_called_once_with(application_role_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(application_role_to_add)
        # Don't need to test the response here because it's just the updated application_role_to_add


class TestGet:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_get_with_data(self, application_role_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await application_role.get_application_role(application_role_id=application_role_id, db=mock_db)

        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, application_role_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await application_role.get_application_role(application_role_id=application_role_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_application_role_found(
        self, application_role_id: int, mock_db: Mock, db_get_return_val: Any
    ) -> None:
        response = await application_role.delete_application_role(application_role_id=application_role_id, db=mock_db)

        mock_db.delete.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_delete_with_application_role_not_found(self, application_role_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await application_role.delete_application_role(application_role_id=application_role_id, db=mock_db)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def application_role_to_update(
        self, application_id: int, role_id: int, application_role_description: str
    ) -> ApplicationRole:
        return ApplicationRole(
            user_id=None, application_id=application_id, role_id=role_id, description=application_role_description
        )

    @pytest.fixture
    def updated_application_role(self) -> ApplicationRoleUpdate:
        return ApplicationRoleUpdate(description="some new description")

    @pytest.mark.parametrize("db_get_return_val", [application_role_to_update])
    async def test_update_with_user_found(
        self,
        application_role_id: int,
        updated_application_role: ApplicationRoleUpdate,
        mock_db: Mock,
        db_get_return_val: ApplicationRole,
    ) -> None:
        response = await application_role.update_application_role(
            application_role_id=application_role_id,
            application_role=updated_application_role,
            db=mock_db,
        )

        mock_db.add.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_get_return_val)
        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        application_role_id: int,
        updated_application_role: ApplicationRoleUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await application_role.update_application_role(
                application_role_id=application_role_id,
                application_role=updated_application_role,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
