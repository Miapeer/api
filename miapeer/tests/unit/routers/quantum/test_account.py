from datetime import date
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import (
    Account,
    AccountCreate,
    AccountUpdate,
)
from miapeer.models.quantum.transaction import Transaction
from miapeer.routers.quantum import account

pytestmark = pytest.mark.asyncio


@pytest.fixture
def account_id() -> int:
    return 12345


@pytest.fixture
def account_name() -> str:
    return "transaction type name"


@pytest.fixture
def starting_balance() -> int:
    return 111


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await account.get_all_accounts(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def account_create(self, account_name: str, portfolio_id: int, starting_balance: int) -> AccountCreate:
        return AccountCreate(name=account_name, portfolio_id=portfolio_id, starting_balance=starting_balance)

    @pytest.fixture
    def account_to_add(self, account_name: str, portfolio_id: int) -> Account:
        return Account(account_id=None, name=account_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def initial_transaction(self, starting_balance: int) -> Transaction:
        return Transaction(
            transaction_type_id=-1,
            payee_id=None,
            category_id=None,
            amount=starting_balance,
            transaction_date=date.today(),
            clear_date=date.today(),
            check_number=None,
            exclude_from_forecast=True,
            notes=None,
        )

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        account_create: AccountCreate,
        account_to_add: Account,
        initial_transaction: Transaction,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await account.create_account(account=account_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_sql

        expected_add_params = [account_to_add.model_dump(), initial_transaction.model_dump()]
        assert mock_db.add.call_count == 2

        actual_add_call_params = [mock_call.args[0].model_dump() for mock_call in mock_db.add.mock_calls]

        assert actual_add_call_params == expected_add_params

        assert mock_db.commit.call_count == 2

        # mock_db.refresh.assert_called_once_with(account_to_add)  # TODO: Try to go back to this once SQLModel can equate models again
        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == account_to_add.model_dump()

        # # Don't need to test the response here because it's just the updated account_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, account_create: AccountCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await account.create_account(account=account_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await account.get_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

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
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

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
    async def test_delete_with_account_not_found(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await account.delete_account(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def account(self, account_name: str, portfolio_id: int) -> Account:
        return Account(account_id=None, name=account_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def updated_account(self) -> AccountUpdate:
        return AccountUpdate(name="some new name")

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [account])
    async def test_update_with_account_found(
        self,
        user: User,
        account_id: int,
        updated_account: AccountUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Account,
    ) -> None:
        response = await account.update_account(
            account_id=account_id,
            account=updated_account,
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
    async def test_update_with_account_not_found(
        self,
        user: User,
        account_id: int,
        updated_account: AccountUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await account.update_account(
                account_id=account_id,
                account=updated_account,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
