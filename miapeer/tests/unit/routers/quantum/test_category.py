from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.category import (
    Category,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)
from miapeer.routers.quantum import category

pytestmark = pytest.mark.asyncio


raw_category_id = 12345


@pytest.fixture
def category_id() -> int:
    return raw_category_id


@pytest.fixture
def category_name() -> str:
    return "transaction type name"


@pytest.fixture
def parent_category_id() -> int:
    return 678


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_category(category_name: str, parent_category_id: int, portfolio_id: int) -> Category:
    return Category(category_id=None, name=category_name, parent_category_id=parent_category_id, portfolio_id=portfolio_id)


@pytest.fixture
def complete_category(category_id: int, basic_category: Category) -> Category:
    return Category.model_validate(basic_category.model_dump(), update={"category_id": category_id})


class TestGetAll:
    @pytest.fixture
    def multiple_categories(self, complete_category: Category) -> list[Category]:
        return [complete_category, complete_category]

    @pytest.fixture
    def expected_multiple_categories(self, complete_category: Category) -> list[CategoryRead]:
        working_category = CategoryRead.model_validate(complete_category)
        return [working_category, working_category]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_categories"), lazy_fixture("expected_multiple_categories"))],
    )
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, expected_response: list[CategoryRead]) -> None:
        response = await category.get_all_categories(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.category_id = raw_category_id

    @pytest.fixture
    def category_to_create(self, category_name: str, parent_category_id: int, portfolio_id: int) -> CategoryCreate:
        return CategoryCreate(name=category_name, parent_category_id=parent_category_id, portfolio_id=portfolio_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        category_to_create: CategoryCreate,
        complete_category: Category,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await category.create_category(category=category_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_category.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_category.model_dump()

        # Don't need to test the response here because it's just the updated category_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(self, user: User, category_to_create: CategoryCreate, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await category.create_category(category=category_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_category: Category) -> CategoryRead:
        return CategoryRead.model_validate(complete_category)

    @pytest.fixture
    def expected_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_category")])
    async def test_get_with_data(self, user: User, category_id: int, mock_db: Mock, expected_sql: str, expected_response: CategoryRead) -> None:
        response = await category.get_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

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
    async def test_delete_with_category_not_found(self, user: User, category_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await category.delete_category(category_id=category_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def category_updates(self, parent_category_id: int) -> CategoryUpdate:
        return CategoryUpdate(name="some new name", parent_category_id=parent_category_id)

    @pytest.fixture
    def expected_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_category(self, complete_category: Category) -> Category:
        return Category.model_validate(complete_category.model_dump(), update={"name": "some new name"})

    @pytest.fixture
    def expected_response(self, updated_category: Category) -> CategoryRead:
        return CategoryRead.model_validate(updated_category.model_dump())

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_category")])
    async def test_update_with_category_found(
        self,
        user: User,
        category_id: int,
        category_updates: CategoryUpdate,
        mock_db: Mock,
        expected_sql: str,
        updated_category: Category,
        expected_response: CategoryRead,
    ) -> None:
        response = await category.update_category(
            category_id=category_id,
            category=category_updates,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_category.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_category.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_category_not_found(
        self,
        user: User,
        category_id: int,
        category_updates: CategoryUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await category.update_category(
                category_id=category_id,
                category=category_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
