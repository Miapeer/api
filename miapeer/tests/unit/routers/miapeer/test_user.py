from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User, UserCreate, UserRead, UserUpdate
from miapeer.routers.miapeer import user

pytestmark = pytest.mark.asyncio

raw_user_id = 12345


@pytest.fixture
def user_id() -> int:
    return raw_user_id


@pytest.fixture
def user_email() -> str:
    return "some email address"


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_user(user_email: str) -> User:
    return User(user_id=None, email=user_email, password="", disabled=False)


@pytest.fixture
def complete_user(user_id: int, basic_user: User) -> User:
    return User.model_validate(basic_user.model_dump(), update={"user_id": user_id})


class TestWhoAmI:
    @pytest.mark.parametrize("return_val", [[], "some data", 123])
    async def test_return_val(self, return_val: Any) -> None:
        response = await user.who_am_i(current_user=return_val)
        assert response == return_val


class TestGetAll:
    @pytest.fixture
    def multiple_users(self, complete_user: User) -> list[User]:
        return [complete_user, complete_user]

    @pytest.fixture
    def expected_multiple_users(self, complete_user: User) -> list[UserRead]:
        working_user = UserRead.model_validate(complete_user)
        return [working_user, working_user]

    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_user.email, miapeer_user.user_id, miapeer_user.password, miapeer_user.disabled \nFROM miapeer_user"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (pytest.lazy_fixture("multiple_users"), pytest.lazy_fixture("expected_multiple_users"))],
    )
    async def test_get_all(self, mock_db: Mock, expected_sql: str, expected_response: list[UserRead]) -> None:
        response = await user.get_all_users(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.user_id = raw_user_id

    @pytest.fixture
    def user_to_create(self, user_email: str) -> UserCreate:
        return UserCreate(email=user_email, disabled=False, password="")

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        user_to_create: UserCreate,
        complete_user: User,
        mock_db: Mock,
    ) -> None:
        await user.create_user(user=user_to_create, db=mock_db)

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_user.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_user.model_dump()

        # Don't need to test the response here because it's just the updated user_to_add


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_user: User) -> UserRead:
        return UserRead.model_validate(complete_user)

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_user")])
    async def test_get_with_data(self, user_id: int, mock_db: Mock, expected_response: UserRead) -> None:
        response = await user.get_user(user_id=user_id, db=mock_db)

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, user_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await user.get_user(user_id=user_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_user_found(self, user_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await user.delete_user(user_id=user_id, db=mock_db)

        mock_db.delete.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_delete_with_user_not_found(self, user_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await user.delete_user(user_id=user_id, db=mock_db)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def user_updates(self) -> UserUpdate:
        return UserUpdate(email="some new email")

    @pytest.fixture
    def updated_user(self, complete_user: User) -> User:
        return User.model_validate(complete_user.model_dump(), update={"email": "some new email"})

    @pytest.fixture
    def expected_response(self, updated_user: User) -> UserRead:
        return UserRead.model_validate(updated_user.model_dump())

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_user")])
    async def test_update_with_user_found(
        self,
        user_id: int,
        user_updates: UserUpdate,
        mock_db: Mock,
        updated_user: User,
        expected_response: UserRead,
    ) -> None:
        response = await user.update_user(
            user_id=user_id,
            user=user_updates,
            db=mock_db,
        )

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_user.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_user.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        user_id: int,
        user_updates: UserUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await user.update_user(
                user_id=user_id,
                user=user_updates,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
