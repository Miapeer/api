from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.repeat_option import RepeatOption
from miapeer.models.quantum.repeat_unit import RepeatUnit
from miapeer.models.quantum.scheduled_transaction import (
    ScheduledTransaction,
    ScheduledTransactionCreate,
    ScheduledTransactionRead,
    ScheduledTransactionUpdate,
)
from miapeer.models.quantum.scheduled_transaction_history import (
    ScheduledTransactionHistory,
)
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
)
from miapeer.routers.quantum import scheduled_transaction

pytestmark = pytest.mark.asyncio


raw_scheduled_transaction_id = 12345


@pytest.fixture
def scheduled_transaction_id() -> int:
    return raw_scheduled_transaction_id


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


@pytest.fixture
def basic_scheduled_transaction(
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
def complete_scheduled_transaction(scheduled_transaction_id: int, basic_scheduled_transaction: ScheduledTransaction) -> ScheduledTransaction:
    return ScheduledTransaction.model_validate(
        basic_scheduled_transaction.model_dump(), update={"scheduled_transaction_id": scheduled_transaction_id}
    )


class TestGetAll:
    @pytest.fixture
    def multiple_scheduled_transactions(self, complete_scheduled_transaction: ScheduledTransaction) -> list[ScheduledTransaction]:
        return [complete_scheduled_transaction, complete_scheduled_transaction]

    @pytest.fixture
    def expected_multiple_scheduled_transactions(self, complete_scheduled_transaction: ScheduledTransaction) -> list[ScheduledTransactionRead]:
        next_transaction = TransactionRead(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=complete_scheduled_transaction.start_date,
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=complete_scheduled_transaction.notes,
            transaction_id=0,
            account_id=complete_scheduled_transaction.account_id,
            balance=None,
        )

        working_scheduled_transaction = ScheduledTransactionRead.model_validate(
            complete_scheduled_transaction.model_dump(), update={"next_transaction": next_transaction}
        )
        return [working_scheduled_transaction, working_scheduled_transaction]

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_scheduled_transaction.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [
            ([], []),
            (
                lazy_fixture("multiple_scheduled_transactions"),
                lazy_fixture("expected_multiple_scheduled_transactions"),
            ),
        ],
    )
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_unit")
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_option")
    async def test_get_all(
        self,
        patched_get_repeat_option: AsyncMock,
        patched_get_repeat_unit: AsyncMock,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: list[ScheduledTransactionRead],
    ) -> None:
        patched_get_repeat_option.return_value = RepeatOption(name="Anually", quantity=10, repeat_unit_id=1, order_index=0)
        patched_get_repeat_unit.return_value = RepeatUnit(name="Year")

        response = await scheduled_transaction.get_all_scheduled_transactions(account_id=account_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.scheduled_transaction_id = raw_scheduled_transaction_id

    @pytest.fixture
    def scheduled_transaction_to_create(
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
    def expected_scheduled_transaction_sql(self, account_id: int, user_id: int) -> str:
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
        scheduled_transaction_to_create: ScheduledTransactionCreate,
        complete_scheduled_transaction: ScheduledTransaction,
        mock_db: Mock,
        expected_scheduled_transaction_sql: str,
        expected_transaction_type_sql: str,
        expected_payee_sql: str,
        expected_category_sql: str,
    ) -> None:
        await scheduled_transaction.create_scheduled_transaction(
            account_id=account_id, scheduled_transaction=scheduled_transaction_to_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args_list[0].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_scheduled_transaction_sql

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
        assert add_call_param.model_dump() == complete_scheduled_transaction.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_scheduled_transaction.model_dump()

        # Don't need to test the response here because it's just the updated scheduled_transaction_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_to_create: ScheduledTransactionCreate,
        mock_db: Mock,
        expected_scheduled_transaction_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.create_scheduled_transaction(
                account_id=account_id,
                scheduled_transaction=scheduled_transaction_to_create,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_scheduled_transaction_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_scheduled_transaction: ScheduledTransaction) -> ScheduledTransactionRead:
        transaction = TransactionRead(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=date(2001, 2, 3),
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=complete_scheduled_transaction.notes,
            transaction_id=0,
            account_id=complete_scheduled_transaction.account_id,
            balance=None,
        )
        return ScheduledTransactionRead.model_validate(complete_scheduled_transaction.model_dump(), update={"next_transaction": transaction})

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int, scheduled_transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_scheduled_transaction.scheduled_transaction_id = {scheduled_transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_scheduled_transaction")])
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_unit")
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_option")
    async def test_get_with_data(
        self,
        patched_get_repeat_option: AsyncMock,
        patched_get_repeat_unit: AsyncMock,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: ScheduledTransactionRead,
    ) -> None:
        patched_get_repeat_option.return_value = RepeatOption(name="Anually", quantity=1, repeat_unit_id=1, order_index=0)
        patched_get_repeat_unit.return_value = RepeatUnit(name="Year")

        response = await scheduled_transaction.get_scheduled_transaction(
            account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_no_data(self, user: User, account_id: int, scheduled_transaction_id: int, mock_db: Mock, expected_sql: str) -> None:
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
    def scheduled_transaction_updates(self, on_autopay: bool) -> ScheduledTransactionUpdate:
        return ScheduledTransactionUpdate(
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
    def expected_scheduled_transaction_sql(self, user_id: int, account_id: int, scheduled_transaction_id: int) -> str:
        return f"SELECT quantum_scheduled_transaction.transaction_type_id, quantum_scheduled_transaction.payee_id, quantum_scheduled_transaction.category_id, quantum_scheduled_transaction.fixed_amount, quantum_scheduled_transaction.estimate_occurrences, quantum_scheduled_transaction.prompt_days, quantum_scheduled_transaction.start_date, quantum_scheduled_transaction.end_date, quantum_scheduled_transaction.limit_occurrences, quantum_scheduled_transaction.repeat_option_id, quantum_scheduled_transaction.notes, quantum_scheduled_transaction.on_autopay, quantum_scheduled_transaction.scheduled_transaction_id, quantum_scheduled_transaction.account_id \nFROM quantum_scheduled_transaction JOIN quantum_account ON quantum_account.account_id = quantum_scheduled_transaction.account_id JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_scheduled_transaction.scheduled_transaction_id = {scheduled_transaction_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_transaction_type_sql(self, user_id: int, scheduled_transaction_updates: ScheduledTransactionUpdate) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {scheduled_transaction_updates.transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_payee_sql(self, user_id: int, scheduled_transaction_updates: ScheduledTransactionUpdate) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {scheduled_transaction_updates.payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def expected_category_sql(self, user_id: int, scheduled_transaction_updates: ScheduledTransactionUpdate) -> str:
        return f"SELECT quantum_category.name, quantum_category.parent_category_id, quantum_category.portfolio_id, quantum_category.category_id \nFROM quantum_category JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_category.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_category.category_id = {scheduled_transaction_updates.category_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_scheduled_transaction(self, complete_scheduled_transaction: ScheduledTransaction) -> ScheduledTransaction:
        return ScheduledTransaction.model_validate(
            complete_scheduled_transaction.model_dump(),
            update={
                "transaction_type_id": 8881,
                "payee_id": 8882,
                "category_id": 8883,
                "fixed_amount": 8884,
                "estimate_occurrences": 8885,
                "prompt_days": 8886,
                "start_date": date.today(),
                "end_date": date.today(),
                "limit_occurrences": 8887,
                "repeat_option_id": 8888,
                "notes": "8889",
                "on_autopay": (not on_autopay),
            },
        )

    @pytest.fixture
    def expected_response(self, updated_scheduled_transaction: ScheduledTransaction) -> ScheduledTransactionRead:
        next_transaction = TransactionRead(
            transaction_type_id=updated_scheduled_transaction.transaction_type_id,
            payee_id=updated_scheduled_transaction.payee_id,
            category_id=updated_scheduled_transaction.category_id,
            amount=updated_scheduled_transaction.fixed_amount if updated_scheduled_transaction.fixed_amount else 0,
            transaction_date=updated_scheduled_transaction.start_date,
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=updated_scheduled_transaction.notes,
            transaction_id=0,
            account_id=updated_scheduled_transaction.account_id,
            balance=None,
        )
        return ScheduledTransactionRead.model_validate(updated_scheduled_transaction.model_dump(), update={"next_transaction": next_transaction})

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_scheduled_transaction")])
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_unit")
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_option")
    async def test_update_with_scheduled_transaction_found(
        self,
        patched_get_repeat_option: AsyncMock,
        patched_get_repeat_unit: AsyncMock,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        scheduled_transaction_updates: ScheduledTransactionUpdate,
        mock_db: Mock,
        expected_scheduled_transaction_sql: str,
        expected_transaction_type_sql: str,
        expected_payee_sql: str,
        expected_category_sql: str,
        updated_scheduled_transaction: ScheduledTransaction,
        expected_response: ScheduledTransactionRead,
    ) -> None:
        patched_get_repeat_option.return_value = RepeatOption(name="Anually", quantity=10, repeat_unit_id=1, order_index=0)
        patched_get_repeat_unit.return_value = RepeatUnit(name="Year")

        response = await scheduled_transaction.update_scheduled_transaction(
            account_id=account_id,
            scheduled_transaction_id=scheduled_transaction_id,
            scheduled_transaction=scheduled_transaction_updates,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args_list[0].args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_scheduled_transaction_sql

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
        assert add_call_param.model_dump() == updated_scheduled_transaction.model_dump()

        mock_db.commit.assert_called_once()

        mock_db.refresh.assert_not_called()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_scheduled_transaction_not_found(
        self,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        scheduled_transaction_updates: ScheduledTransactionUpdate,
        mock_db: Mock,
        expected_scheduled_transaction_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await scheduled_transaction.update_scheduled_transaction(
                account_id=account_id,
                scheduled_transaction_id=scheduled_transaction_id,
                scheduled_transaction=scheduled_transaction_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_scheduled_transaction_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestNextIteration:
    @pytest.mark.parametrize(
        "start_date, end_date, repeat_option, repeat_unit, expected_transaction_dates",
        [
            (
                date(year=2001, month=2, day=3),
                date(year=2001, month=3, day=20),
                RepeatOption(name="Weekly", quantity=7, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Day"),
                [
                    date(year=2001, month=2, day=3),
                    date(year=2001, month=2, day=10),
                    date(year=2001, month=2, day=17),
                    date(year=2001, month=2, day=24),
                    date(year=2001, month=3, day=3),
                    date(year=2001, month=3, day=10),
                    date(year=2001, month=3, day=17),
                ],
            ),
            (
                date(year=2001, month=2, day=3),
                date(year=2001, month=3, day=20),
                RepeatOption(name="Bi-Weekly", quantity=14, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Day"),
                [
                    date(year=2001, month=2, day=3),
                    date(year=2001, month=2, day=17),
                    date(year=2001, month=3, day=3),
                    date(year=2001, month=3, day=17),
                ],
            ),
            (
                date(year=2001, month=2, day=3),
                date(year=2001, month=4, day=20),
                RepeatOption(name="Semi-Monthly", quantity=0, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Semi-Month"),
                [
                    date(year=2001, month=2, day=16),
                    date(year=2001, month=3, day=1),
                    date(year=2001, month=3, day=16),
                    date(year=2001, month=4, day=1),
                    date(year=2001, month=4, day=16),
                ],
            ),
            (
                date(year=1999, month=12, day=31),
                date(year=2000, month=4, day=30),
                RepeatOption(name="Monthly", quantity=1, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Month"),
                [
                    date(year=1999, month=12, day=31),
                    date(year=2000, month=1, day=31),
                    date(year=2000, month=2, day=29),
                    date(year=2000, month=3, day=29),
                    date(year=2000, month=4, day=29),
                ],
            ),
            (
                date(year=2001, month=2, day=3),
                date(year=2002, month=7, day=20),
                RepeatOption(name="Quarterly", quantity=3, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Month"),
                [
                    date(year=2001, month=2, day=3),
                    date(year=2001, month=5, day=3),
                    date(year=2001, month=8, day=3),
                    date(year=2001, month=11, day=3),
                    date(year=2002, month=2, day=3),
                    date(year=2002, month=5, day=3),
                ],
            ),
            (
                date(year=2001, month=2, day=3),
                date(year=2003, month=7, day=20),
                RepeatOption(name="Semi-Anually", quantity=6, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Month"),
                [
                    date(year=2001, month=2, day=3),
                    date(year=2001, month=8, day=3),
                    date(year=2002, month=2, day=3),
                    date(year=2002, month=8, day=3),
                    date(year=2003, month=2, day=3),
                ],
            ),
            (
                date(year=2000, month=2, day=29),
                date(year=2002, month=2, day=28),
                RepeatOption(name="Anually", quantity=1, repeat_unit_id=1, order_index=0),
                RepeatUnit(name="Year"),
                [date(year=2000, month=2, day=29), date(year=2001, month=2, day=28), date(year=2002, month=2, day=28)],
            ),
        ],
    )
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_unit")
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_option")
    async def test_next_iterations_with_reasonable_end_date(
        self,
        patched_get_repeat_option: AsyncMock,
        patched_get_repeat_unit: AsyncMock,
        mock_db: Mock,
        complete_scheduled_transaction: ScheduledTransaction,
        start_date: date,
        end_date: date,
        repeat_option: RepeatOption,
        repeat_unit: RepeatUnit,
        expected_transaction_dates: list[date],
    ) -> None:
        patched_get_repeat_option.return_value = repeat_option
        patched_get_repeat_unit.return_value = repeat_unit

        results = await scheduled_transaction.get_next_iterations(
            db=mock_db,
            scheduled_transaction=ScheduledTransaction.model_validate(
                complete_scheduled_transaction.model_dump(), update={"start_date": start_date, "end_date": end_date}
            ),
        )

        assert len(results) == len(expected_transaction_dates)

        for index, result in enumerate(results):
            assert result.transaction_date == expected_transaction_dates[index]

    @patch("miapeer.routers.quantum.repeat_option.get_repeat_unit")
    @patch("miapeer.routers.quantum.repeat_option.get_repeat_option")
    async def test_next_iterations_with_limit(
        self,
        patched_get_repeat_option: AsyncMock,
        patched_get_repeat_unit: AsyncMock,
        mock_db: Mock,
        complete_scheduled_transaction: ScheduledTransaction,
    ) -> None:
        patched_get_repeat_option.return_value = RepeatOption(name="Anually", quantity=10, repeat_unit_id=1, order_index=0)
        patched_get_repeat_unit.return_value = RepeatUnit(name="Year")

        set_limit = 10

        results = await scheduled_transaction.get_next_iterations(
            db=mock_db,
            scheduled_transaction=ScheduledTransaction.model_validate(
                complete_scheduled_transaction.model_dump(),
                update={"start_date": date(year=2001, month=1, day=1), "end_date": date(year=3000, month=1, day=1)},
            ),
            override_limit=set_limit,
        )

        assert len(results) == set_limit

    async def test_next_iterations_with_no_repeat(
        self,
        mock_db: Mock,
        complete_scheduled_transaction: ScheduledTransaction,
    ) -> None:
        results = await scheduled_transaction.get_next_iterations(
            db=mock_db,
            scheduled_transaction=ScheduledTransaction.model_validate(
                complete_scheduled_transaction.model_dump(), update={"repeat_option_id": None, "end_date": date(year=3000, month=1, day=1)}
            ),
        )

        expected = Transaction(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=complete_scheduled_transaction.start_date,
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=complete_scheduled_transaction.notes,
            account_id=complete_scheduled_transaction.account_id,
            transaction_id=None,
        )

        assert len(results) == 1
        assert results[0].model_dump() == expected.model_dump()


class TestCreateTransaction:
    @pytest.fixture
    def scheduled_transaction_with_no_next(self, complete_scheduled_transaction) -> ScheduledTransactionRead:
        return ScheduledTransactionRead.model_validate(complete_scheduled_transaction)

    @pytest.fixture
    def scheduled_transaction_with_next(self, complete_scheduled_transaction: ScheduledTransaction) -> ScheduledTransactionRead:
        next_transaction = TransactionRead(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=complete_scheduled_transaction.start_date,
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=complete_scheduled_transaction.notes,
            transaction_id=0,
            account_id=complete_scheduled_transaction.account_id,
            balance=None,
        )

        return ScheduledTransactionRead.model_validate(
            complete_scheduled_transaction.model_dump(),
            update={
                "next_transaction": next_transaction,
            },
        )

    @pytest.fixture
    def base_transaction_to_create(self, complete_scheduled_transaction: ScheduledTransaction) -> Transaction:
        return Transaction(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=complete_scheduled_transaction.start_date,
            clear_date=None,
            check_number=None,
            exclude_from_forecast=False,
            notes=complete_scheduled_transaction.notes,
            account_id=complete_scheduled_transaction.account_id,
            transaction_id=0,
        )

    @pytest.fixture
    def base_transaction_created(self, base_transaction_to_create: Transaction):
        return TransactionRead(
            transaction_type_id=base_transaction_to_create.transaction_type_id,
            payee_id=base_transaction_to_create.payee_id,
            category_id=base_transaction_to_create.category_id,
            amount=base_transaction_to_create.amount,
            transaction_date=base_transaction_to_create.transaction_date,
            clear_date=base_transaction_to_create.clear_date,
            check_number=base_transaction_to_create.check_number,
            exclude_from_forecast=base_transaction_to_create.exclude_from_forecast,
            notes=base_transaction_to_create.notes,
            transaction_id=0,
            account_id=base_transaction_to_create.account_id if base_transaction_to_create.account_id else 0,
            balance=None,
        )

    @pytest.fixture
    def transaction_overrides_1(self) -> TransactionCreate:
        return TransactionCreate(
            transaction_type_id=131,
            category_id=133,
            transaction_date=date(year=2000, month=2, day=22),
            check_number="135",
            notes="overridden note",
        )

    @pytest.fixture
    def transaction_overrides_2(self) -> TransactionCreate:
        return TransactionCreate(
            payee_id=132,
            amount=134,
            clear_date=None,
            exclude_from_forecast=True,
        )

    @pytest.fixture
    def transaction_to_create_with_overrides_1(
        self, complete_scheduled_transaction: ScheduledTransaction, transaction_overrides_1: TransactionCreate
    ) -> Transaction:
        return Transaction(
            transaction_type_id=transaction_overrides_1.transaction_type_id,
            payee_id=complete_scheduled_transaction.payee_id,
            category_id=transaction_overrides_1.category_id,
            amount=complete_scheduled_transaction.fixed_amount if complete_scheduled_transaction.fixed_amount else 0,
            transaction_date=transaction_overrides_1.transaction_date,
            clear_date=None,
            check_number=transaction_overrides_1.check_number,
            exclude_from_forecast=False,
            notes=transaction_overrides_1.notes,
            account_id=complete_scheduled_transaction.account_id,
            transaction_id=0,
        )

    @pytest.fixture
    def transaction_to_create_with_overrides_2(
        self, complete_scheduled_transaction: ScheduledTransaction, transaction_overrides_2: TransactionCreate
    ) -> Transaction:
        return Transaction(
            transaction_type_id=complete_scheduled_transaction.transaction_type_id,
            payee_id=transaction_overrides_2.payee_id,
            category_id=complete_scheduled_transaction.category_id,
            amount=transaction_overrides_2.amount,
            transaction_date=complete_scheduled_transaction.start_date,
            clear_date=transaction_overrides_2.clear_date,
            check_number=None,
            exclude_from_forecast=transaction_overrides_2.exclude_from_forecast,
            notes=complete_scheduled_transaction.notes,
            account_id=complete_scheduled_transaction.account_id,
            transaction_id=0,
        )

    @pytest.fixture
    def transaction_with_overrides_created_1(self, transaction_to_create_with_overrides_1: Transaction):
        return TransactionRead(
            transaction_type_id=transaction_to_create_with_overrides_1.transaction_type_id,
            payee_id=transaction_to_create_with_overrides_1.payee_id,
            category_id=transaction_to_create_with_overrides_1.category_id,
            amount=transaction_to_create_with_overrides_1.amount,
            transaction_date=transaction_to_create_with_overrides_1.transaction_date,
            clear_date=transaction_to_create_with_overrides_1.clear_date,
            check_number=transaction_to_create_with_overrides_1.check_number,
            exclude_from_forecast=transaction_to_create_with_overrides_1.exclude_from_forecast,
            notes=transaction_to_create_with_overrides_1.notes,
            transaction_id=0,
            account_id=transaction_to_create_with_overrides_1.account_id if transaction_to_create_with_overrides_1.account_id else 0,
            balance=None,
        )

    @pytest.fixture
    def transaction_with_overrides_created_2(self, transaction_to_create_with_overrides_2: Transaction):
        return TransactionRead(
            transaction_type_id=transaction_to_create_with_overrides_2.transaction_type_id,
            payee_id=transaction_to_create_with_overrides_2.payee_id,
            category_id=transaction_to_create_with_overrides_2.category_id,
            amount=transaction_to_create_with_overrides_2.amount,
            transaction_date=transaction_to_create_with_overrides_2.transaction_date,
            clear_date=transaction_to_create_with_overrides_2.clear_date,
            check_number=transaction_to_create_with_overrides_2.check_number,
            exclude_from_forecast=transaction_to_create_with_overrides_2.exclude_from_forecast,
            notes=transaction_to_create_with_overrides_2.notes,
            transaction_id=0,
            account_id=transaction_to_create_with_overrides_2.account_id if transaction_to_create_with_overrides_2.account_id else 0,
            balance=None,
        )

    @pytest.fixture
    def scheduled_transaction_history_record(
        self, complete_scheduled_transaction: ScheduledTransaction, base_transaction_to_create: Transaction
    ) -> ScheduledTransactionHistory:
        return ScheduledTransactionHistory(
            target_date=complete_scheduled_transaction.start_date,
            post_date=date.today(),
            scheduled_transaction_id=complete_scheduled_transaction.scheduled_transaction_id
            if complete_scheduled_transaction.scheduled_transaction_id
            else 0,
            transaction_id=base_transaction_to_create.transaction_id if base_transaction_to_create.transaction_id else 0,
            scheduled_transaction_history_id=None,
        )

    @patch("miapeer.routers.quantum.scheduled_transaction.get_scheduled_transaction")
    async def test_create_transaction_fails(
        self,
        patched_get_scheduled_transaction: AsyncMock,
        mock_db: Mock,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        scheduled_transaction_with_no_next: ScheduledTransactionRead,
    ) -> None:
        patched_get_scheduled_transaction.return_value = scheduled_transaction_with_no_next

        with pytest.raises(HTTPException):
            await scheduled_transaction.create_transaction(
                db=mock_db,
                current_user=user,
                account_id=account_id,
                scheduled_transaction_id=scheduled_transaction_id,
                override_transaction_data=None,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    @pytest.mark.parametrize(
        "override_transaction_data, transaction_to_create, expected_response",
        [
            (
                None,
                lazy_fixture("base_transaction_to_create"),
                lazy_fixture("base_transaction_created"),
            ),
            (
                lazy_fixture("transaction_overrides_1"),
                lazy_fixture("transaction_to_create_with_overrides_1"),
                lazy_fixture("transaction_with_overrides_created_1"),
            ),
            (
                lazy_fixture("transaction_overrides_2"),
                lazy_fixture("transaction_to_create_with_overrides_2"),
                lazy_fixture("transaction_with_overrides_created_2"),
            ),
        ],
    )
    @patch("miapeer.routers.quantum.scheduled_transaction.get_scheduled_transaction")
    @patch("miapeer.routers.quantum.scheduled_transaction.progress_iteration")
    async def test_create_transaction_succeeds(
        self,
        patched_progress_iteration: AsyncMock,
        patched_get_scheduled_transaction: AsyncMock,
        mock_db: Mock,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        scheduled_transaction_with_next: ScheduledTransactionRead,
        override_transaction_data: TransactionCreate,
        transaction_to_create: Transaction,
        scheduled_transaction_history_record: ScheduledTransactionHistory,
        expected_response: TransactionRead,
    ) -> None:
        patched_get_scheduled_transaction.return_value = scheduled_transaction_with_next

        response = await scheduled_transaction.create_transaction(
            db=mock_db,
            current_user=user,
            account_id=account_id,
            scheduled_transaction_id=scheduled_transaction_id,
            override_transaction_data=override_transaction_data,
        )
        assert response == expected_response

        assert mock_db.add.call_count == 2

        add_call_param = mock_db.add.call_args_list[0].args[0]
        assert add_call_param.model_dump() == transaction_to_create.model_dump()

        add_call_param = mock_db.add.call_args_list[1].args[0]
        assert add_call_param.model_dump() == scheduled_transaction_history_record.model_dump()

        assert mock_db.commit.call_count == 2

        assert mock_db.refresh.call_count == 1

        refresh_call_param = mock_db.refresh.call_args_list[0].args[0]
        assert refresh_call_param.model_dump() == transaction_to_create.model_dump()

        patched_progress_iteration.assert_called_once()


class TestProgressIteration:
    @pytest.fixture
    def updated_scheduled_transaction_with_next(
        self, complete_scheduled_transaction: ScheduledTransactionRead, next_transactions: list[Transaction]
    ) -> ScheduledTransaction:
        return ScheduledTransaction.model_validate(
            complete_scheduled_transaction.model_dump(), update={"start_date": next_transactions[1].transaction_date}
        )

    @pytest.fixture
    def updated_scheduled_transaction_with_no_next(
        self, complete_scheduled_transaction: ScheduledTransactionRead, next_transactions: list[Transaction]
    ) -> ScheduledTransaction:
        return ScheduledTransaction.model_validate(
            complete_scheduled_transaction.model_dump(), update={"start_date": scheduled_transaction.MAX_END_DATE}
        )

    @pytest.mark.parametrize(
        "next_transactions, updated_scheduled_transaction",
        [
            (  # Happy path
                [Transaction(transaction_date=date(year=111, month=1, day=1)), Transaction(transaction_date=date(year=222, month=1, day=1))],
                lazy_fixture("updated_scheduled_transaction_with_next"),
            ),
            (  # There's a current transaction, but not a next
                [Transaction(transaction_date=date(year=111, month=1, day=1))],
                lazy_fixture("updated_scheduled_transaction_with_no_next"),
            ),
            (  # No next iterations at all
                [],
                lazy_fixture("updated_scheduled_transaction_with_no_next"),
            ),
        ],
    )
    @patch("miapeer.routers.quantum.scheduled_transaction.get_scheduled_transaction")
    @patch("miapeer.routers.quantum.scheduled_transaction.get_next_iterations")
    async def test_scheduled_transaction_has_correct_next_iteration(
        self,
        patched_get_next_iterations: AsyncMock,
        patched_get_scheduled_transaction: AsyncMock,
        mock_db: Mock,
        user: User,
        account_id: int,
        scheduled_transaction_id: int,
        complete_scheduled_transaction: ScheduledTransactionRead,
        next_transactions: list[Transaction],
        updated_scheduled_transaction: ScheduledTransaction,
    ) -> None:
        patched_get_scheduled_transaction.return_value = complete_scheduled_transaction
        patched_get_next_iterations.return_value = next_transactions

        await scheduled_transaction.progress_iteration(
            db=mock_db,
            current_user=user,
            account_id=account_id,
            scheduled_transaction_id=scheduled_transaction_id,
        )

        mock_db.add.assert_called_once()

        add_call_param = mock_db.add.call_args_list[0].args[0]
        assert add_call_param.model_dump() == updated_scheduled_transaction.model_dump()

        mock_db.commit.assert_called_once()
