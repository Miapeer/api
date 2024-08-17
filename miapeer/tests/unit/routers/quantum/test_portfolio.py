from typing import Any
from unittest.mock import Mock, call

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioRead,
)
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.routers.quantum import portfolio

pytestmark = pytest.mark.asyncio


raw_portfolio_id = 12345


@pytest.fixture
def portfolio_id() -> int:
    return raw_portfolio_id


@pytest.fixture
def basic_portfolio() -> Portfolio:
    return Portfolio(portfolio_id=None)


@pytest.fixture
def complete_portfolio(portfolio_id: int, basic_portfolio: Portfolio) -> Portfolio:
    return Portfolio.model_validate(basic_portfolio.model_dump(), update={"portfolio_id": portfolio_id})


class TestGetAll:
    @pytest.fixture
    def multiple_portfolios(self, complete_portfolio: Portfolio) -> list[Portfolio]:
        return [complete_portfolio, complete_portfolio]

    @pytest.fixture
    def expected_multiple_portfolios(self, complete_portfolio: Portfolio) -> list[PortfolioRead]:
        working_portfolio = PortfolioRead.model_validate(complete_portfolio)
        return [working_portfolio, working_portfolio]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_portfolios"), lazy_fixture("expected_multiple_portfolios"))],
    )
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, expected_response: list[PortfolioRead]) -> None:
        response = await portfolio.get_all_portfolios(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.portfolio_id = raw_portfolio_id

    @pytest.fixture
    def portfolio_to_create(self) -> PortfolioCreate:
        return PortfolioCreate()

    @pytest.fixture
    def portfolio_to_add(self) -> PortfolioRead:
        return PortfolioRead(portfolio_id=984)

    @pytest.fixture
    def portfolio_user_to_add(self, portfolio_id: int, user_id: int) -> PortfolioUser:
        return PortfolioUser(portfolio_id=portfolio_id, user_id=user_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        portfolio_to_create: PortfolioCreate,
        complete_portfolio: Portfolio,
        portfolio_user_to_add: PortfolioUser,
        mock_db: Mock,
    ) -> None:
        await portfolio.create_portfolio(portfolio=portfolio_to_create, db=mock_db, current_user=user)

        expected_add_params = [
            complete_portfolio.model_dump(),
            portfolio_user_to_add.model_dump(),
        ]
        assert mock_db.add.call_count == 2

        actual_add_call_params = [mock_call.args[0].model_dump() for mock_call in mock_db.add.mock_calls]
        assert actual_add_call_params == expected_add_params

        assert mock_db.commit.call_count == 2

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_portfolio.model_dump()

        # Don't need to test the response here because it's just the updated portfolio_to_add


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_portfolio: Portfolio) -> PortfolioRead:
        return PortfolioRead.model_validate(complete_portfolio)

    @pytest.fixture
    def expected_sql(self, user_id: int, portfolio_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio.portfolio_id = {portfolio_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_portfolio")])
    async def test_get_with_data(self, user: User, portfolio_id: int, mock_db: Mock, expected_sql: str, expected_response: PortfolioRead) -> None:
        response = await portfolio.get_portfolio(portfolio_id=portfolio_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

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

    @pytest.mark.parametrize("db_get_return_val, db_all_return_val", [("a portfolio", ["some data"]), ("a portfolio", [123, 456])])
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
    async def test_delete_with_portfolio_not_found(self, user: User, portfolio_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await portfolio.delete_portfolio(portfolio_id=portfolio_id, db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
