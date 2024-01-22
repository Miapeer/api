from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User, UserCreate, UserUpdate
from miapeer.routers.miapeer import user

pytestmark = pytest.mark.asyncio


@pytest.fixture
def user_id() -> int:
    return 12345


@pytest.fixture
def user_email() -> str:
    return "some email address"


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestWhoAmI:
    @pytest.mark.parametrize("return_val", [[], "some data", 123])
    async def test_return_val(self, return_val: Any) -> None:
        response = await user.who_am_i(current_user=return_val)
        assert response == return_val


class TestGetAll:
    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_user.email, miapeer_user.user_id, miapeer_user.password, miapeer_user.disabled \nFROM miapeer_user"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await user.get_all_users(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def user_create(self, user_email: str) -> UserCreate:
        return UserCreate(email=user_email)

    @pytest.fixture
    def user_to_add(self, user_email: str) -> User:
        return User(user_id=None, email=user_email, password="", disabled=False)

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        user_create: UserCreate,
        user_to_add: User,
        mock_db: Mock,
    ) -> None:
        await user.create_user(user=user_create, db=mock_db)

        mock_db.add.assert_called_once_with(user_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user_to_add)
        # Don't need to test the response here because it's just the updated user_to_add


class TestGet:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_get_with_data(self, user_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await user.get_user(user_id=user_id, db=mock_db)

        assert response == db_get_return_val

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
    def user_to_update(self, user_email: str, portfolio_id: int) -> User:
        return User(user_id=None, email=user_email, portfolio_id=portfolio_id)

    @pytest.fixture
    def updated_user(self) -> UserUpdate:
        return UserUpdate(email="some new email")

    @pytest.mark.parametrize("db_get_return_val", [user_to_update])
    async def test_update_with_user_found(
        self,
        user_id: int,
        updated_user: UserUpdate,
        mock_db: Mock,
        db_get_return_val: User,
    ) -> None:
        response = await user.update_user(
            user_id=user_id,
            user=updated_user,
            db=mock_db,
        )

        mock_db.add.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_get_return_val)
        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        user_id: int,
        updated_user: UserUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await user.update_user(
                user_id=user_id,
                user=updated_user,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
