from datetime import date
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.scheduled_transaction import (
    ScheduledTransaction,
    ScheduledTransactionCreate,
    ScheduledTransactionUpdate,
)
from miapeer.routers.quantum import scheduled_transaction

pytestmark = pytest.mark.asyncio


@pytest.fixture
def scheduled_transaction_id() -> int:
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
def fixed_amount() -> int:
    return 444


@pytest.fixture
def estimate_occurrences() -> int:
    return 555


@pytest.fixture
def prompt_days() -> int:
    return 666


@pytest.fixture
def start_date() -> date:
    return date(year=2001, month=2, day=3)


@pytest.fixture
def end_date() -> date:
    return date(year=2011, month=12, day=13)


@pytest.fixture
def limit_occurrences() -> int:
    return 777


@pytest.fixture
def repeat_option_id() -> int:
    return 888


@pytest.fixture
def notes() -> str:
    return "some notes"


@pytest.fixture
def on_autopay() -> bool:
    return True


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_scheduled_transaction.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str, db_all_return_val: Any
    ) -> None:
        response = await scheduled_transaction.get_all_scheduled_transactions(
            account_id=account_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def scheduled_transaction_create(
        self,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: date,
        end_date: date,
        limit_occurrences: int,
        repeat_option_id: int,
        notes: str,
        on_autopay: bool,
    ) -> ScheduledTransactionCreate:
        return ScheduledTransactionCreate(
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            fixed_amount=fixed_amount,
            estimate_occurrences=estimate_occurrences,
            prompt_days=prompt_days,
            start_date=start_date,
            end_date=end_date,
            limit_occurrences=limit_occurrences,
            repeat_option_id=repeat_option_id,
            notes=notes,
            on_autopay=on_autopay,
        )

    @pytest.fixture
    def scheduled_transaction_to_add(
        self,
        account_id: int,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: date,
        end_date: date,
        limit_occurrences: int,
        repeat_option_id: int,
        notes: str,
        on_autopay: bool,
    ) -> ScheduledTransaction:
        return ScheduledTransaction(
            scheduled_transaction_id=None,
            account_id=account_id,
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            fixed_amount=fixed_amount,
            estimate_occurrences=estimate_occurrences,
            prompt_days=prompt_days,
            start_date=start_date,
            end_date=end_date,
            limit_occurrences=limit_occurrences,
            repeat_option_id=repeat_option_id,
            notes=notes,
            on_autopay=on_autopay,
        )

    @pytest.fixture
    def expected_sql(self, account_id: int, user_id: int) -> str:
        return f"SELECT quantum_account.name, quantum_account.portfolio_id, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_create: ScheduledTransactionCreate,
        scheduled_transaction_to_add: ScheduledTransaction,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await scheduled_transaction.create_scheduled_transaction(
            account_id=account_id, scheduled_transaction=scheduled_transaction_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(scheduled_transaction_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(scheduled_transaction_to_add)
        # Don't need to test the response here because it's just the updated scheduled_transaction_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_create: ScheduledTransactionCreate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.create_scheduled_transaction(
                account_id=account_id,
                scheduled_transaction=scheduled_transaction_create,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, scheduled_transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_scheduled_transaction.scheduled_transaction_id = {scheduled_transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await scheduled_transaction.get_scheduled_transaction(
            account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_no_data(
        self, user: User, account_id: int, scheduled_transaction_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.get_scheduled_transaction(
                account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, scheduled_transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_scheduled_transaction.scheduled_transaction_id = {scheduled_transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_scheduled_transaction_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await scheduled_transaction.delete_scheduled_transaction(
            account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_scheduled_transaction_not_found(
        self, user: User, account_id: int, scheduled_transaction_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.delete_scheduled_transaction(
                account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def scheduled_transaction(
        self,
        account_id: int,
        transaction_type_id: int,
        payee_id: int,
        category_id: int,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: date,
        end_date: date,
        limit_occurrences: int,
        repeat_option_id: int,
        notes: str,
        on_autopay: bool,
    ) -> ScheduledTransaction:
        return ScheduledTransaction(
            scheduled_transaction_id=None,
            account_id=account_id,
            transaction_type_id=transaction_type_id,
            payee_id=payee_id,
            category_id=category_id,
            fixed_amount=fixed_amount,
            estimate_occurrences=estimate_occurrences,
            prompt_days=prompt_days,
            start_date=start_date,
            end_date=end_date,
            limit_occurrences=limit_occurrences,
            repeat_option_id=repeat_option_id,
            notes=notes,
            on_autopay=on_autopay,
        )

    @pytest.fixture
    def updated_scheduled_transaction(self, on_autopay: bool) -> ScheduledTransactionUpdate:
        return ScheduledTransactionUpdate(
            scheduled_transaction_id=None,
            transaction_type_id=8881,
            payee_id=8882,
            category_id=8883,
            fixed_amount=8884,
            estimate_occurrences=8885,
            prompt_days=8886,
            start_date=date.today(),
            end_date=date.today(),
            limit_occurrences=8887,
            repeat_option_id=8888,
            notes="8889",
            on_autopay=(not on_autopay),
        )

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, scheduled_transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_scheduled_transaction.scheduled_transaction_id = {scheduled_transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [scheduled_transaction])
    async def test_update_with_scheduled_transaction_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        updated_scheduled_transaction: ScheduledTransactionUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: ScheduledTransaction,
    ) -> None:
        response = await scheduled_transaction.update_scheduled_transaction(
            account_id=account_id,
            scheduled_transaction_id=scheduled_transaction_id,
            scheduled_transaction=updated_scheduled_transaction,
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
    async def test_update_with_scheduled_transaction_not_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        updated_scheduled_transaction: ScheduledTransactionUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.update_scheduled_transaction(
                account_id=account_id,
                scheduled_transaction_id=scheduled_transaction_id,
                scheduled_transaction=updated_scheduled_transaction,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
