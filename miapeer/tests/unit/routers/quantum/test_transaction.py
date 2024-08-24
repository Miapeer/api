import random
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from miapeer.routers.quantum import transaction

pytestmark = pytest.mark.asyncio

raw_transaction_id = 12345


@pytest.fixture
def transaction_id() -> int:
    return raw_transaction_id


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
    return 0


@pytest.fixture
def transaction_date() -> date:
    return date(year=2001, month=2, day=3)


@pytest.fixture
def clear_date() -> date:
    return date(year=2011, month=12, day=13)


@pytest.fixture
def check_number() -> str:
    return "555"


@pytest.fixture
def exclude_from_forecast() -> bool:
    return True


@pytest.fixture
def notes() -> str:
    return "some notes"


@pytest.fixture
def basic_transaction(
    account_id: int,
    transaction_type_id: int,
    payee_id: int,
    category_id: int,
    amount: int,
    transaction_date: date,
    clear_date: date,
    check_number: str,
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
def complete_transaction(transaction_id: int, basic_transaction: Transaction) -> Transaction:
    return Transaction.model_validate(basic_transaction.model_dump(), update={"transaction_id": transaction_id})


class TestGetAll:
    @pytest.fixture
    def multiple_transactions(self, complete_transaction: Transaction) -> list[Transaction]:
        return [complete_transaction, complete_transaction]

    @pytest.fixture
    def expected_multiple_transactions(self, complete_transaction: Transaction) -> list[TransactionRead]:
        working_transaction = TransactionRead.model_validate(complete_transaction.model_dump(), update={"balance": 0})
        return [working_transaction, working_transaction]

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        limit_date = date(year=date.today().year, month=date.today().month, day=1)
        limit_date -= relativedelta(months=6)
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.account_id, quantum_transaction.transaction_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id} AND (quantum_transaction.clear_date IS NULL OR quantum_transaction.clear_date >= '{limit_date}')"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_transactions"), lazy_fixture("expected_multiple_transactions"))],
    )
    @patch("miapeer.routers.quantum.account.get_account")
    async def test_get_all(
        self,
        get_account_patch: AsyncMock,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: list[TransactionRead],
    ) -> None:
        get_account_patch.return_value = Account(portfolio_id=0, name="", starting_balance=0)

        response = await transaction.get_all_transactions(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.transaction_id = raw_transaction_id

    @pytest.fixture
    def transaction_to_create(
        self,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        amount: int,
        transaction_date: date,
        clear_date: date,
        check_number: str,
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
    def expected_transaction_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_transaction_type_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_payee_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_category_sql(self, user_id: int, category_id: int) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        user: User,
        account_id: int,
        transaction_to_create: TransactionCreate,
        complete_transaction: Transaction,
        mock_db: Mock,
        expected_transaction_sql: str,
        expected_transaction_type_sql: str,
        expected_payee_sql: str,
        expected_category_sql: str,
    ) -> None:
        await transaction.create_transaction(account_id=account_id, transaction=transaction_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args_list[0].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_sql

        sql = mock_db.exec.call_args_list[1].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_type_sql

        sql = mock_db.exec.call_args_list[2].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_payee_sql

        sql = mock_db.exec.call_args_list[3].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_category_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_transaction.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_transaction.model_dump()

        # Don't need to test the response here because it's just the updated transaction_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self,
        user: User,
        account_id: int,
        transaction_to_create: TransactionCreate,
        mock_db: Mock,
        expected_transaction_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.create_transaction(account_id=account_id, transaction=transaction_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_transaction_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_transaction: Transaction) -> TransactionRead:
        return TransactionRead.model_validate(complete_transaction)

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.account_id, quantum_transaction.transaction_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_transaction")])
    async def test_get_with_data(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: TransactionRead,
    ) -> None:
        response = await transaction.get_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_no_data(self, user: User, account_id: int, transaction_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await transaction.get_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.account_id, quantum_transaction.transaction_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

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
        response = await transaction.delete_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

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
            await transaction.delete_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def transaction_updates(self, exclude_from_forecast: bool) -> TransactionUpdate:
        return TransactionUpdate(
            transaction_type_id=8881,
            payee_id=8882,
            category_id=8883,
            amount=8884,
            transaction_date=date.today(),
            clear_date=date.today(),
            check_number="8887",
            exclude_from_forecast=(not exclude_from_forecast),
            notes="8888",
        )

    @pytest.fixture
    def expected_transaction_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.account_id, quantum_transaction.transaction_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_transaction_type_sql(self, user_id: int, transaction_updates: TransactionUpdate) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_updates.transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_payee_sql(self, user_id: int, transaction_updates: TransactionUpdate) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {transaction_updates.payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_category_sql(self, user_id: int, transaction_updates: TransactionUpdate) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {transaction_updates.category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_transaction(self, complete_transaction: Transaction) -> Transaction:
        return Transaction.model_validate(
            complete_transaction.model_dump(),
            update={
                "transaction_type_id": 8881,
                "payee_id": 8882,
                "category_id": 8883,
                "amount": 8884,
                "transaction_date": date.today(),
                "clear_date": date.today(),
                "check_number": "8887",
                "exclude_from_forecast": not exclude_from_forecast,
                "notes": "8888",
            },
        )

    @pytest.fixture
    def expected_response(self, updated_transaction: Transaction) -> TransactionRead:
        return TransactionRead.model_validate(updated_transaction.model_dump())

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_transaction")])
    async def test_update_with_transaction_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        transaction_updates: TransactionUpdate,
        mock_db: Mock,
        expected_transaction_sql: str,
        expected_transaction_type_sql: str,
        expected_payee_sql: str,
        expected_category_sql: str,
        updated_transaction: Transaction,
        expected_response: TransactionRead,
    ) -> None:
        response = await transaction.update_transaction(
            account_id=account_id,
            transaction_id=transaction_id,
            transaction=transaction_updates,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args_list[0].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_sql

        sql = mock_db.exec.call_args_list[1].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_type_sql

        sql = mock_db.exec.call_args_list[2].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_payee_sql

        sql = mock_db.exec.call_args_list[3].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_category_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_transaction.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_transaction.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_transaction_not_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        transaction_updates: TransactionUpdate,
        mock_db: Mock,
        expected_transaction_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.update_transaction(
                account_id=account_id,
                transaction_id=transaction_id,
                transaction=transaction_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_transaction_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestRunningBalance:
    @pytest.fixture
    def starting_balance(self) -> int:
        return random.randint(-9999, 9999)

    @pytest.fixture
    def transaction_amounts(self) -> list[int]:
        return [random.randint(-9999, 9999) for _ in range(10)]

    def create_transaction(self, base_transaction: Transaction, amount: int) -> Transaction:
        return Transaction.model_validate(base_transaction.model_dump(), update={"amount": amount})

    @pytest.fixture
    def db_all_return_val(self, transaction_amounts: list[int], complete_transaction: Transaction) -> list[Transaction]:
        return [self.create_transaction(base_transaction=complete_transaction, amount=amount) for amount in transaction_amounts]

    @pytest.fixture
    def expected_transactions(
        self, starting_balance: int, transaction_amounts: list[int], complete_transaction: Transaction
    ) -> list[TransactionRead]:
        running_balance = starting_balance
        working_transactions: list[TransactionRead] = []

        for transaction_amount in transaction_amounts:
            running_balance += transaction_amount
            working_transactions.append(
                TransactionRead.model_validate(
                    complete_transaction.model_dump(),
                    update={"amount": transaction_amount, "balance": running_balance},
                )
            )

        return working_transactions

    @pytest.mark.usefixtures("db_all_return_val")
    @patch("miapeer.routers.quantum.account.get_account")
    async def test_transaction_running_balance(
        self,
        get_account_patch: AsyncMock,
        starting_balance: int,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_transactions: list[TransactionRead],
    ) -> None:
        get_account_patch.return_value = Account(portfolio_id=0, name="", starting_balance=starting_balance)

        response = await transaction.get_all_transactions(account_id=account_id, db=mock_db, current_user=user)
        assert response == expected_transactions
