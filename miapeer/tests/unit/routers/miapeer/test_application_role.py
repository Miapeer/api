from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import (
    ApplicationRole,
    ApplicationRoleCreate,
    ApplicationRoleRead,
    ApplicationRoleUpdate,
)
from miapeer.routers.miapeer import application_role

pytestmark = pytest.mark.asyncio


raw_application_role_id: int = 8302


@pytest.fixture
def application_role_id() -> int:
    return raw_application_role_id


@pytest.fixture
def application_id() -> int:
    return 111


@pytest.fixture
def role_id() -> int:
    return 222


@pytest.fixture
def application_role_description() -> str:
    return "a_r desc"


@pytest.fixture
def basic_application_role(application_id: int, role_id: int, application_role_description: str) -> ApplicationRole:
    return ApplicationRole(
        application_role_id=None,
        application_id=application_id,
        role_id=role_id,
        description=application_role_description,
    )


@pytest.fixture
def complete_application_role(application_role_id: int, basic_application_role: ApplicationRole) -> ApplicationRole:
    return ApplicationRole.model_validate(
        basic_application_role.model_dump(), update={"application_role_id": application_role_id}
    )


class TestGetAll:
    @pytest.fixture
    def multiple_application_roles(self, complete_application_role: ApplicationRole) -> list[ApplicationRole]:
        return [complete_application_role, complete_application_role]

    @pytest.fixture
    def expected_multiple_application_roles(
        self, complete_application_role: ApplicationRole
    ) -> list[ApplicationRoleRead]:
        working_application_role = ApplicationRoleRead.model_validate(complete_application_role)
        return [working_application_role, working_application_role]

    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_application_role.application_id, miapeer_application_role.role_id, miapeer_application_role.description, miapeer_application_role.application_role_id \nFROM miapeer_application_role"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_application_roles"), lazy_fixture("expected_multiple_application_roles"))],
    )
    async def test_get_all(
        self, mock_db: Mock, expected_sql: str, expected_response: list[ApplicationRoleRead]
    ) -> None:
        response = await application_role.get_all_application_roles(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:
        obj.application_role_id = raw_application_role_id

    @pytest.fixture
    def application_role_to_create(self, basic_application_role: ApplicationRole) -> ApplicationRoleCreate:
        return ApplicationRoleCreate.model_validate(basic_application_role)

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        application_role_to_create: ApplicationRoleCreate,
        complete_application_role: ApplicationRole,
        mock_db: Mock,
    ) -> None:
        await application_role.create_application_role(application_role=application_role_to_create, db=mock_db)

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_application_role.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_application_role.model_dump()

        # Don't need to test the response here because it's just the updated basic_application_role


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_application_role: ApplicationRole) -> ApplicationRoleRead:
        return ApplicationRoleRead.model_validate(complete_application_role)

    @pytest.mark.parametrize("db_get_return_val", [lazy_fixture("complete_application_role")])
    async def test_get_with_data(
        self, application_role_id: int, mock_db: Mock, expected_response: ApplicationRoleRead
    ) -> None:
        response = await application_role.get_application_role(application_role_id=application_role_id, db=mock_db)

        assert response == expected_response

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
    def application_role_updates(self) -> ApplicationRoleUpdate:
        return ApplicationRoleUpdate(description="some new description")

    @pytest.fixture
    def updated_application_role(self, complete_application_role: ApplicationRole) -> ApplicationRole:
        return ApplicationRole.model_validate(
            complete_application_role.model_dump(), update={"description": "some new description"}
        )

    @pytest.fixture
    def expected_response(self, updated_application_role: ApplicationRole) -> ApplicationRoleRead:
        return ApplicationRoleRead.model_validate(updated_application_role.model_dump())

    @pytest.mark.parametrize("db_get_return_val", [lazy_fixture("complete_application_role")])
    async def test_update_with_user_found(
        self,
        application_role_id: int,
        application_role_updates: ApplicationRoleUpdate,
        mock_db: Mock,
        updated_application_role: ApplicationRole,
        expected_response: ApplicationRoleRead,
    ) -> None:
        response = await application_role.update_application_role(
            application_role_id=application_role_id,
            application_role=application_role_updates,
            db=mock_db,
        )

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_application_role.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_application_role.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        application_role_id: int,
        application_role_updates: ApplicationRoleUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await application_role.update_application_role(
                application_role_id=application_role_id,
                application_role=application_role_updates,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
