from typing import Any
from unittest.mock import Mock, call

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.portfolio import Portfolio, PortfolioCreate
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.routers.quantum import portfolio

pytestmark = pytest.mark.asyncio


@pytest.fixture
def portfolio_id() -> int:
    return 12345


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await portfolio.get_all_portfolios(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def portfolio_create(self, portfolio_id: int) -> PortfolioCreate:
        return PortfolioCreate(portfolio_id=portfolio_id)

    @pytest.fixture
    def portfolio_to_add(self) -> Portfolio:
        return Portfolio()

    @pytest.fixture
    def portfolio_user_to_add(self, user_id: int) -> PortfolioUser:
        return PortfolioUser(user_id=user_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        portfolio_create: PortfolioCreate,
        portfolio_to_add: Portfolio,
        portfolio_user_to_add: PortfolioUser,
        mock_db: Mock,
    ) -> None:
        await portfolio.create_portfolio(portfolio=portfolio_create, db=mock_db, current_user=user)

        expected_add_calls = [
            call(portfolio_to_add),
            call(portfolio_user_to_add),
        ]
        assert mock_db.add.call_count == 2
        assert mock_db.add.mock_calls == expected_add_calls

        assert mock_db.commit.call_count == 2

        mock_db.refresh.assert_called_once_with(portfolio_to_add)
        # Don't need to test the response here because it's just the updated portfolio_to_add


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, portfolio_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio.portfolio_id = {portfolio_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self, user: User, portfolio_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await portfolio.get_portfolio(portfolio_id=portfolio_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(self, user: User, portfolio_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await portfolio.get_portfolio(portfolio_id=portfolio_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, portfolio_id: int) -> str:
        return f"SELECT quantum_portfolio_user.portfolio_id, quantum_portfolio_user.user_id, quantum_portfolio_user.portfolio_user_id \nFROM quantum_portfolio_user \nWHERE quantum_portfolio_user.portfolio_id = {portfolio_id}"

    @pytest.mark.parametrize(
        "db_get_return_val, db_all_return_val", [("a portfolio", ["some data"]), ("a portfolio", [123, 456])]
    )
    async def test_delete_with_portfolio_found(
        self, portfolio_id: int, mock_db: Mock, expected_sql: str, db_get_return_val: Any, db_all_return_val: Any
    ) -> None:
        response = await portfolio.delete_portfolio(
            portfolio_id=portfolio_id,
            db=mock_db,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.delete.call_count == len(db_all_return_val) + 1

        expected_delete_calls = [call(db_get_return_val)] + [call(x) for x in db_all_return_val]
        assert mock_db.delete.mock_calls == expected_delete_calls

        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_portfolio_not_found(
        self, user: User, portfolio_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await portfolio.delete_portfolio(portfolio_id=portfolio_id, db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
