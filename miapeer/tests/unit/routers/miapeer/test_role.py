from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import Role, RoleCreate, RoleRead, RoleUpdate
from miapeer.routers.miapeer import role

pytestmark = pytest.mark.asyncio


raw_role_id = 12345


@pytest.fixture
def role_id() -> int:
    return raw_role_id


@pytest.fixture
def role_name() -> str:
    return "some role"


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_role(role_name: str) -> Role:
    return Role(role_id=None, name=role_name)


@pytest.fixture
def complete_role(role_id: int, basic_role: Role) -> Role:
    return Role.model_validate(basic_role.model_dump(), update={"role_id": role_id})


class TestGetAll:
    @pytest.fixture
    def multiple_roles(self, complete_role: Role) -> list[Role]:
        return [complete_role, complete_role]

    @pytest.fixture
    def expected_multiple_roles(self, complete_role: Role) -> list[RoleRead]:
        working_role = RoleRead.model_validate(complete_role)
        return [working_role, working_role]

    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_role.name, miapeer_role.role_id \nFROM miapeer_role"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (pytest.lazy_fixture("multiple_roles"), pytest.lazy_fixture("expected_multiple_roles"))],
    )
    async def test_get_all(self, mock_db: Mock, expected_sql: str, expected_response: list[RoleRead]) -> None:
        response = await role.get_all_roles(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.role_id = raw_role_id

    @pytest.fixture
    def role_to_create(self, role_name: str) -> RoleCreate:
        return RoleCreate(name=role_name)

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        role_to_create: RoleCreate,
        complete_role: Role,
        mock_db: Mock,
    ) -> None:
        await role.create_role(role=role_to_create, db=mock_db)

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_role.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_role.model_dump()

        # Don't need to test the response here because it's just the updated role_to_add


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_role: Role) -> RoleRead:
        return RoleRead.model_validate(complete_role)

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_role")])
    async def test_get_with_data(self, role_id: int, mock_db: Mock, expected_response: RoleRead) -> None:
        response = await role.get_role(role_id=role_id, db=mock_db)

        assert response == expected_response

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
    def role_updates(self) -> RoleUpdate:
        return RoleUpdate(name="some new name")

    @pytest.fixture
    def updated_role(self, complete_role: Role) -> Role:
        return Role.model_validate(complete_role.model_dump(), update={"name": "some new name"})

    @pytest.fixture
    def expected_response(self, updated_role: Role) -> RoleRead:
        return RoleRead.model_validate(updated_role.model_dump())

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_role")])
    async def test_update_with_role_found(
        self,
        role_id: int,
        role_updates: RoleUpdate,
        mock_db: Mock,
        updated_role: Role,
        expected_response: RoleRead,
    ) -> None:
        response = await role.update_role(
            role_id=role_id,
            role=role_updates,
            db=mock_db,
        )

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_role.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_role.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_role_not_found(
        self,
        role_id: int,
        role_updates: RoleUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await role.update_role(
                role_id=role_id,
                role=role_updates,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
