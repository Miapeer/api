from datetime import date
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
from miapeer.routers.quantum import transaction

pytestmark = pytest.mark.asyncio


@pytest.fixture
def transaction_id() -> int:
    return 12345


@pytest.fixture
def account_id() -> int:
    return 345


@pytest.fixture
def transaction_type_id() -> int:
    return 111


@pytest.fixture
def payee_id() -> int:
    return 222


@pytest.fixture
def category_id() -> int:
    return 333


@pytest.fixture
def amount() -> int:
    return 444


@pytest.fixture
def transaction_date() -> date:
    return date(year=2001, month=2, day=3)


@pytest.fixture
def clear_date() -> date:
    return date(year=2011, month=12, day=13)


@pytest.fixture
def check_number() -> int:
    return 555


@pytest.fixture
def exclude_from_forecast() -> bool:
    return True


@pytest.fixture
def notes() -> str:
    return "some notes"


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.transaction_id, quantum_transaction.account_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str, db_all_return_val: Any
    ) -> None:
        response = await transaction.get_all_transactions(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def transaction_create(
        self,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        amount: int,
        transaction_date: date,
        clear_date: date,
        check_number: int,
        exclude_from_forecast: bool,
        notes: str,
    ) -> TransactionCreate:
        return TransactionCreate(
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            amount=amount,
            transaction_date=transaction_date,
            clear_date=clear_date,
            check_number=check_number,
            exclude_from_forecast=exclude_from_forecast,
            notes=notes,
        )

    @pytest.fixture
    def transaction_to_add(
        self,
        account_id: int,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        amount: int,
        transaction_date: date,
        clear_date: date,
        check_number: int,
        exclude_from_forecast: bool,
        notes: str,
    ) -> Transaction:
        return Transaction(
            transaction_id=None,
            account_id=account_id,
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            amount=amount,
            transaction_date=transaction_date,
            clear_date=clear_date,
            check_number=check_number,
            exclude_from_forecast=exclude_from_forecast,
            notes=notes,
        )

    @pytest.fixture
    def expected_sql(self, account_id: int, user_id: int) -> str:
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        user: User,
        account_id: int,
        transaction_create: TransactionCreate,
        transaction_to_add: Transaction,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await transaction.create_transaction(
            account_id=account_id, transaction=transaction_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(transaction_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(transaction_to_add)
        # Don't need to test the response here because it's just the updated transaction_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, account_id: int, transaction_create: TransactionCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.create_transaction(
                account_id=account_id, transaction=transaction_create, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.transaction_id, quantum_transaction.account_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await transaction.get_transaction(
            account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        print(f"{sql_str=}\n")  # TODO: Remove this!!!

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_no_data(
        self, user: User, account_id: int, transaction_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.get_transaction(
                account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.transaction_id, quantum_transaction.account_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_transaction_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await transaction.delete_transaction(
            account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_transaction_not_found(
        self, user: User, account_id: int, transaction_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.delete_transaction(
                account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def transaction(
        self,
        account_id: int,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        amount: int,
        transaction_date: date,
        clear_date: date,
        check_number: int,
        exclude_from_forecast: bool,
        notes: str,
    ) -> Transaction:
        return Transaction(
            transaction_id=None,
            account_id=account_id,
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            amount=amount,
            transaction_date=transaction_date,
            clear_date=clear_date,
            check_number=check_number,
            exclude_from_forecast=exclude_from_forecast,
            notes=notes,
        )

    @pytest.fixture
    def updated_transaction(self, exclude_from_forecast: bool) -> TransactionUpdate:
        return TransactionUpdate(
            transaction_id=None,
            transaction_type_id=8881,
            payee_id=8882,
            category_id=8883,
            amount=8884,
            transaction_date=date.today(),
            clear_date=date.today(),
            check_number=8887,
            exclude_from_forecast=(not exclude_from_forecast),
            notes="8888",
        )

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.transaction_id, quantum_transaction.account_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [transaction])
    async def test_update_with_transaction_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        updated_transaction: TransactionUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Transaction,
    ) -> None:
        response = await transaction.update_transaction(
            account_id=account_id,
            transaction_id=transaction_id,
            transaction=updated_transaction,
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
    async def test_update_with_transaction_not_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        updated_transaction: TransactionUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.update_transaction(
                account_id=account_id,
                transaction_id=transaction_id,
                transaction=updated_transaction,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
