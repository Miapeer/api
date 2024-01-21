from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
)
from miapeer.routers.quantum import category

pytestmark = pytest.mark.asyncio


@pytest.fixture
def category_id() -> int:
    return 12345


@pytest.fixture
def category_name() -> str:
    return "transaction type name"


@pytest.fixture
def parent_category_id() -> int:
    return 678


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await category.get_all_categories(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def category_create(self, category_name: str, parent_category_id: int, portfolio_id: int) -> CategoryCreate:
        return CategoryCreate(name=category_name, parent_category_id=parent_category_id, portfolio_id=portfolio_id)

    @pytest.fixture
    def category_to_add(self, category_name: str, parent_category_id: int, portfolio_id: int) -> Category:
        return Category(
            category_id=None, name=category_name, parent_category_id=parent_category_id, portfolio_id=portfolio_id
        )

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        category_create: CategoryCreate,
        category_to_add: Category,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await category.create_category(category=category_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(category_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(category_to_add)
        # Don't need to test the response here because it's just the updated category_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, category_create: CategoryCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await category.create_category(category=category_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self, user: User, category_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await category.get_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(self, user: User, category_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await category.get_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_category_found(
        self, user: User, category_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await category.delete_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_category_not_found(
        self, user: User, category_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await category.delete_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def category(self, category_name: str, portfolio_id: int) -> Category:
        return Category(category_id=None, name=category_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def updated_category(self) -> CategoryUpdate:
        return CategoryUpdate(name="some new name")

    @pytest.fixture
    def expected_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [category])
    async def test_update_with_category_found(
        self,
        user: User,
        category_id: int,
        updated_category: CategoryUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Category,
    ) -> None:
        response = await category.update_category(
            category_id=category_id,
            category=updated_category,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_one_or_none_return_val)
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_category_not_found(
        self,
        user: User,
        category_id: int,
        updated_category: CategoryUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await category.update_category(
                category_id=category_id,
                category=updated_category,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
