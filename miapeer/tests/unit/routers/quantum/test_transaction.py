import random
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException

from miapeer.adapter.sql import transaction as transaction_sql
from miapeer.models.miapeer import User
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from miapeer.models.quantum.transaction_type import TransactionType
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


@pytest.fixture
def account_name() -> str:
    return "transaction type name"


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_account(account_id: int, account_name: str, portfolio_id: int) -> Account:
    return Account(account_id=account_id, name=account_name, portfolio_id=portfolio_id, starting_balance=0)


@dataclass
class DbTransaction:
    transaction_type_id: Optional[int]
    payee_id: Optional[int]
    category_id: Optional[int]
    amount: int
    transaction_date: date
    clear_date: Optional[date]
    check_number: Optional[str]
    exclude_from_forecast: bool
    notes: Optional[str]
    account_id: Optional[int]
    transaction_id: Optional[int]
    order_index: int


def create_db_transaction(base_transaction: Transaction, override_amount: Optional[int] = None, order_index: int = 1) -> DbTransaction:
    transaction = DbTransaction(**base_transaction.model_dump(), order_index=order_index)
    if override_amount is not None:
        transaction.amount = override_amount
    return transaction


class TestGetAll:
    @pytest.fixture
    def multiple_transactions(self, complete_transaction: Transaction) -> list[Transaction]:
        return [create_db_transaction(base_transaction=complete_transaction), create_db_transaction(base_transaction=complete_transaction)]

    @pytest.fixture
    def expected_multiple_transactions(self, complete_transaction: Transaction) -> list[TransactionRead]:
        working_transaction = TransactionRead.model_validate(complete_transaction.model_dump(), update={"balance": 0})
        return [working_transaction, working_transaction]

    @pytest.fixture
    def expected_sql_date(self) -> date:
        limit_date = date(year=date.today().year, month=date.today().month, day=1)
        limit_date -= relativedelta(months=3)
        return limit_date

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [
            ([], []),
            # (pytest.lazy_fixture("multiple_transactions"), pytest.lazy_fixture("expected_multiple_transactions"))
        ],
    )
    @patch("miapeer.routers.quantum.transaction._get_forecasted_transactions")
    @patch("miapeer.routers.quantum.account.get_account")
    async def test_get_all(
        self,
        get_account_patch: AsyncMock,
        get_forcasted_transactions_patch: AsyncMock,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql_date: date,
        expected_response: list[TransactionRead],
    ) -> None:
        get_account_patch.return_value = Account(portfolio_id=0, name="", starting_balance=0)
        get_forcasted_transactions_patch.return_value = []

        response = await transaction.get_all_transactions(account_id=account_id, db=mock_db, current_user=user)

        mock_db.exec.assert_called_with(
            transaction_sql.GET_ALL, params={"account_id": account_id, "user_id": user.user_id, "limit_date": expected_sql_date}
        )
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

    @pytest.fixture
    def db_first_return_values(self, basic_account, transaction_type_id, payee_id, category_id) -> list:
        return [
            basic_account,
            Transaction(transaction_type_id=transaction_type_id),
            Payee(payee_id=payee_id),
            Category(category_id=category_id),
            "some data",
        ]

    @pytest.mark.parametrize("db_first_side_effect_val, db_refresh_patch_method", [(pytest.lazy_fixture("db_first_return_values"), db_refresh)])
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

    @pytest.mark.parametrize("db_one_or_none_return_val", [pytest.lazy_fixture("complete_transaction")])
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
    def expected_transaction_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_transaction.transaction_type_id, quantum_transaction.payee_id, quantum_transaction.category_id, quantum_transaction.amount, quantum_transaction.transaction_date, quantum_transaction.clear_date, quantum_transaction.check_number, quantum_transaction.exclude_from_forecast, quantum_transaction.notes, quantum_transaction.account_id, quantum_transaction.transaction_id \nFROM quantum_transaction JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_transaction.transaction_id = {transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_scheduled_transaction_history_sql(self, transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction_history.target_date, quantum_scheduled_transaction_history.post_date, quantum_scheduled_transaction_history.scheduled_transaction_id, quantum_scheduled_transaction_history.transaction_id, quantum_scheduled_transaction_history.scheduled_transaction_history_id \nFROM quantum_scheduled_transaction_history \nWHERE quantum_scheduled_transaction_history.transaction_id = {transaction_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_transaction_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        mock_db: Mock,
        expected_transaction_sql: str,
        expected_scheduled_transaction_history_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await transaction.delete_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args_list[0].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_sql

        sql = mock_db.exec.call_args_list[1].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_scheduled_transaction_history_sql

        # Twice, because the "one_or_none" return value will be returned for both transaction and scheduled_transaction_history DB calls
        expected_delete_calls = [call(db_one_or_none_return_val)] + [call(db_one_or_none_return_val)]
        assert mock_db.delete.mock_calls == expected_delete_calls

        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_transaction_not_found(
        self, user: User, account_id: int, transaction_id: int, mock_db: Mock, expected_transaction_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction.delete_transaction(account_id=account_id, transaction_id=transaction_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_transaction_sql
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
    def expected_account_sql(self, user_id: int, account_id: int, transaction_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

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

    @pytest.fixture
    def db_first_return_values(self, basic_account, updated_transaction) -> list:
        return [
            basic_account,
            TransactionType(transaction_type_id=updated_transaction.transaction_type_id),
            Payee(payee_id=updated_transaction.payee_id),
            Category(category_id=updated_transaction.category_id),
        ]

    @pytest.mark.parametrize(
        "db_one_or_none_return_val, db_first_side_effect_val",
        [(pytest.lazy_fixture("complete_transaction"), pytest.lazy_fixture("db_first_return_values"))],
    )
    async def test_update_with_transaction_found(
        self,
        user: User,
        account_id: int,
        transaction_id: int,
        transaction_updates: TransactionUpdate,
        mock_db: Mock,
        expected_transaction_sql: str,
        expected_account_sql: str,
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
        assert sql_str == expected_account_sql

        sql = mock_db.exec.call_args_list[2].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_transaction_type_sql

        sql = mock_db.exec.call_args_list[3].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_payee_sql

        sql = mock_db.exec.call_args_list[4].args[0]
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

    @pytest.fixture
    def db_all_return_val(self, transaction_amounts: list[int], complete_transaction: Transaction, starting_balance: int) -> list[DbTransaction]:
        starting_balance_transaction = create_db_transaction(base_transaction=complete_transaction, override_amount=starting_balance, order_index=-2)
        return [starting_balance_transaction] + [
            create_db_transaction(base_transaction=complete_transaction, override_amount=amount) for amount in transaction_amounts
        ]

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
    @patch("miapeer.routers.quantum.transaction._get_forecasted_transactions")
    async def test_transaction_running_balance(
        self,
        get_forcasted_transactions_patch: AsyncMock,
        starting_balance: int,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_transactions: list[TransactionRead],
    ) -> None:
        get_forcasted_transactions_patch.return_value = []

        response = await transaction.get_all_transactions(account_id=account_id, db=mock_db, current_user=user)
        assert response == expected_transactions
