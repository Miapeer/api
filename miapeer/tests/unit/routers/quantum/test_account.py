from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import (
    Account,
    AccountCreate,
    AccountRead,
    AccountUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.routers.quantum import account

pytestmark = pytest.mark.asyncio


raw_account_id = 12345


@pytest.fixture
def account_id() -> int:
    return raw_account_id


@pytest.fixture
def account_name() -> str:
    return "transaction type name"


@pytest.fixture
def starting_balance() -> int:
    return 111


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_account(account_name: str, portfolio_id: int) -> Account:
    return Account(account_id=None, name=account_name, portfolio_id=portfolio_id, starting_balance=0)


@pytest.fixture
def complete_account(account_id: int, basic_account: Account, starting_balance: int) -> Account:
    return Account.model_validate(basic_account.model_dump(), update={"account_id": account_id, "starting_balance": starting_balance})


class TestGetAll:
    @pytest.fixture
    def multiple_accounts(self, complete_account: Account) -> list[Account]:
        return [complete_account, complete_account]

    @pytest.fixture
    def expected_multiple_accounts(self, complete_account: Account, starting_balance: int) -> list[AccountRead]:
        working_account = AccountRead.model_validate(complete_account.model_dump(), update={"balance": starting_balance})
        return [working_account, working_account]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_accounts"), lazy_fixture("expected_multiple_accounts"))],
    )
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, expected_response: list[AccountRead], starting_balance: int) -> None:
        with patch("miapeer.routers.quantum.account.get_account_balance", lambda x, y: starting_balance):
            response = await account.get_all_accounts(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.account_id = raw_account_id

    @pytest.fixture
    def portfolio(self, portfolio_id: int) -> Portfolio:
        return Portfolio(portfolio_id=portfolio_id)

    @pytest.fixture
    def account_to_create(self, account_name: str, portfolio_id: int, starting_balance: int) -> AccountCreate:
        return AccountCreate(name=account_name, portfolio_id=portfolio_id, starting_balance=starting_balance)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [(lazy_fixture("portfolio"), db_refresh)])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        account_to_create: AccountCreate,
        complete_account: Account,
        mock_db: Mock,
        expected_sql: str,
        starting_balance: int,
    ) -> None:
        with patch("miapeer.routers.quantum.account.get_account_balance", lambda x, y: starting_balance):
            await account.create_account(account=account_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_sql

        expected_add_params = [complete_account.model_dump()]
        assert mock_db.add.call_count == 1

        actual_add_call_params = [mock_call.args[0].model_dump() for mock_call in mock_db.add.mock_calls]

        assert actual_add_call_params == expected_add_params

        assert mock_db.commit.call_count == 1

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_account.model_dump()

        # Don't need to test the response here because it's just the updated account_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(self, user: User, account_to_create: AccountCreate, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await account.create_account(account=account_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_account: Account, starting_balance: int) -> AccountRead:
        return AccountRead.model_validate(complete_account.model_dump(), update={"balance": starting_balance})

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_account")])
    async def test_get_with_data(
        self,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: AccountRead,
        starting_balance: int,
    ) -> None:
        with patch("miapeer.routers.quantum.account.get_account_balance", lambda x, y: starting_balance):
            response = await account.get_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(self, user: User, account_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await account.get_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_account_found(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await account.delete_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_account_not_found(self, user: User, account_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await account.delete_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def account_updates(self, starting_balance: int) -> AccountUpdate:
        return AccountUpdate(name="some new name", starting_balance=starting_balance)

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_account(self, complete_account: Account) -> Account:
        return Account.model_validate(complete_account.model_dump(), update={"name": "some new name"})

    @pytest.fixture
    def expected_response(self, updated_account: Account, starting_balance: int) -> AccountRead:
        return AccountRead.model_validate(updated_account.model_dump(), update={"starting_balance": starting_balance, "balance": starting_balance})

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_account")])
    async def test_update_with_account_found(
        self,
        user: User,
        account_id: int,
        account_updates: AccountUpdate,
        mock_db: Mock,
        expected_sql: str,
        updated_account: Account,
        expected_response: AccountRead,
        starting_balance: int,
    ) -> None:

        with patch("miapeer.routers.quantum.account.get_account_balance", lambda x, y: starting_balance):
            response = await account.update_account(
                account_id=account_id,
                account=account_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_account.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_account.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_account_not_found(
        self,
        user: User,
        account_id: int,
        account_updates: AccountUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await account.update_account(
                account_id=account_id,
                account=account_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
