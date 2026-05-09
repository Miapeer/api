from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import (
    Account,
    AccountCreate,
    AccountRead,
    AccountUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.transaction_summary import TransactionSummary
from miapeer.routers.quantum import account
from pytest_lazy_fixtures import lf as lazy_fixture

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
    return Account(
        account_id=None,
        name=account_name,
        portfolio_id=portfolio_id,
        starting_balance=0,
    )


@pytest.fixture
def complete_account(
    account_id: int, basic_account: Account, starting_balance: int
) -> Account:
    return Account.model_validate(
        basic_account.model_dump(),
        update={"account_id": account_id, "starting_balance": starting_balance},
    )


class TestGetAccountBalance:
    @pytest.fixture
    def summary_year(self) -> int:
        return 2023

    @pytest.fixture
    def summary_month(self) -> int:
        return 10

    @pytest.fixture
    def summary_balance(self) -> int:
        return 500

    @pytest.fixture
    def transaction_summary(
        self,
        account_id: int,
        summary_year: int,
        summary_month: int,
        summary_balance: int,
    ) -> TransactionSummary:
        return TransactionSummary(
            account_id=account_id,
            year=summary_year,
            month=summary_month,
            balance=summary_balance,
        )

    @pytest.fixture
    def transaction_summaries(
        self, transaction_summary: TransactionSummary
    ) -> list[TransactionSummary]:
        return [transaction_summary]

    @pytest.fixture
    def expected_summaries_sql(self, account_id: int) -> str:
        return (
            f"SELECT quantum_transaction_summary.account_id, quantum_transaction_summary.year, "
            f"quantum_transaction_summary.month, quantum_transaction_summary.balance, "
            f"quantum_transaction_summary.transaction_summary_id \nFROM quantum_transaction_summary "
            f"JOIN quantum_account ON quantum_account.account_id = quantum_transaction_summary.account_id "
            f"JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id "
            f"JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id "
            f"\nWHERE quantum_account.account_id = {account_id} "
            f"ORDER BY quantum_transaction_summary.year DESC, quantum_transaction_summary.month DESC"
        )

    @pytest.fixture
    def expected_transaction_sum_sql_no_summaries(self, account_id: int) -> str:
        return (
            f"SELECT sum(quantum_transaction.amount) AS sum_1 \nFROM quantum_transaction "
            f"JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id "
            f"JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id "
            f"JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id "
            f"\nWHERE quantum_account.account_id = {account_id}"
        )

    @pytest.fixture
    def expected_transaction_sum_sql_with_summaries(
        self, account_id: int, summary_year: int, summary_month: int
    ) -> str:
        return (
            f"SELECT sum(quantum_transaction.amount) AS sum_1 \nFROM quantum_transaction "
            f"JOIN quantum_account ON quantum_account.account_id = quantum_transaction.account_id "
            f"JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id "
            f"JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id "
            f"\nWHERE quantum_account.account_id = {account_id} AND "
            f"(quantum_transaction.clear_date IS NULL OR "
            f"EXTRACT(year FROM quantum_transaction.clear_date) > {summary_year} OR "
            f"EXTRACT(year FROM quantum_transaction.clear_date) = {summary_year} AND "
            f"EXTRACT(month FROM quantum_transaction.clear_date) > {summary_month})"
        )

    @pytest.mark.parametrize(
        "db_first_return_val, expected_balance",
        [
            (None, lazy_fixture("starting_balance")),
            (250, 361),  # starting_balance (111) + transaction_sum (250)
        ],
    )
    def test_get_account_balance_with_no_summaries(
        self,
        complete_account: Account,
        mock_db: Mock,
        expected_summaries_sql: str,
        expected_transaction_sum_sql_no_summaries: str,
        expected_balance: int,
    ) -> None:
        result = account.get_account_balance(db=mock_db, account=complete_account)

        summaries_sql = mock_db.exec.call_args_list[0].args[0]
        summaries_sql_str = str(
            summaries_sql.compile(compile_kwargs={"literal_binds": True})
        )
        assert summaries_sql_str == expected_summaries_sql

        transaction_sum_sql = mock_db.exec.call_args_list[1].args[0]
        transaction_sum_sql_str = str(
            transaction_sum_sql.compile(compile_kwargs={"literal_binds": True})
        )
        assert transaction_sum_sql_str == expected_transaction_sum_sql_no_summaries

        assert result == expected_balance

    @pytest.mark.parametrize(
        "db_fetchall_return_val, db_first_return_val, expected_balance",
        [
            (
                lazy_fixture("transaction_summaries"),
                None,
                611,
            ),  # starting_balance (111) + summary_balance (500)
            (
                lazy_fixture("transaction_summaries"),
                250,
                861,
            ),  # starting_balance (111) + summary_balance (500) + transaction_sum (250)
        ],
    )
    def test_get_account_balance_with_summaries(
        self,
        complete_account: Account,
        mock_db: Mock,
        expected_summaries_sql: str,
        expected_transaction_sum_sql_with_summaries: str,
        expected_balance: int,
    ) -> None:
        result = account.get_account_balance(db=mock_db, account=complete_account)

        summaries_sql = mock_db.exec.call_args_list[0].args[0]
        summaries_sql_str = str(
            summaries_sql.compile(compile_kwargs={"literal_binds": True})
        )
        assert summaries_sql_str == expected_summaries_sql

        transaction_sum_sql = mock_db.exec.call_args_list[1].args[0]
        transaction_sum_sql_str = str(
            transaction_sum_sql.compile(compile_kwargs={"literal_binds": True})
        )
        assert transaction_sum_sql_str == expected_transaction_sum_sql_with_summaries

        assert result == expected_balance


class TestGetAll:
    @pytest.fixture
    def multiple_accounts(self, complete_account: Account) -> list[Account]:
        return [complete_account, complete_account]

    @pytest.fixture
    def expected_multiple_accounts(
        self, complete_account: Account, starting_balance: int
    ) -> list[AccountRead]:
        working_account = AccountRead.model_validate(
            complete_account.model_dump(), update={"balance": starting_balance}
        )
        return [working_account, working_account]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [
            ([], []),
            (
                lazy_fixture("multiple_accounts"),
                lazy_fixture("expected_multiple_accounts"),
            ),
        ],
    )
    @patch("miapeer.routers.quantum.account.get_account_balance")
    async def test_get_all(
        self,
        patched_get_account_balance: Mock,
        user: User,
        mock_db: Mock,
        expected_sql: str,
        expected_response: list[AccountRead],
        starting_balance: int,
    ) -> None:
        patched_get_account_balance.return_value = starting_balance

        response = await account.get_all_accounts(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:
        obj.account_id = raw_account_id

    @pytest.fixture
    def portfolio(self, portfolio_id: int) -> Portfolio:
        return Portfolio(portfolio_id=portfolio_id)

    @pytest.fixture
    def account_to_create(
        self, account_name: str, portfolio_id: int, starting_balance: int
    ) -> AccountCreate:
        return AccountCreate(
            name=account_name,
            portfolio_id=portfolio_id,
            starting_balance=starting_balance,
        )

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_first_return_val, db_refresh_patch_method",
        [(lazy_fixture("portfolio"), db_refresh)],
    )
    @patch("miapeer.routers.quantum.account.get_account_balance")
    async def test_create_with_portfolio_found(
        self,
        patched_get_account_balance: Mock,
        user: User,
        account_to_create: AccountCreate,
        complete_account: Account,
        mock_db: Mock,
        expected_sql: str,
        starting_balance: int,
    ) -> None:
        patched_get_account_balance.return_value = starting_balance

        await account.create_account(
            account=account_to_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))
        assert sql_str == expected_sql

        expected_add_params = [complete_account.model_dump()]
        assert mock_db.add.call_count == 1

        actual_add_call_params = [
            mock_call.args[0].model_dump() for mock_call in mock_db.add.mock_calls
        ]

        assert actual_add_call_params == expected_add_params

        assert mock_db.commit.call_count == 1

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_account.model_dump()

        # Don't need to test the response here because it's just the updated account_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self,
        user: User,
        account_to_create: AccountCreate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await account.create_account(
                account=account_to_create, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(
        self, complete_account: Account, starting_balance: int
    ) -> AccountRead:
        return AccountRead.model_validate(
            complete_account.model_dump(), update={"balance": starting_balance}
        )

    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_one_or_none_return_val", [lazy_fixture("complete_account")]
    )
    @patch("miapeer.routers.quantum.account.get_account_balance")
    async def test_get_with_data(
        self,
        patched_get_account_balance: Mock,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: AccountRead,
        starting_balance: int,
    ) -> None:
        patched_get_account_balance.return_value = starting_balance

        response = await account.get_account(
            account_id=account_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(
        self, user: User, account_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await account.get_account(
                account_id=account_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, account_id: int) -> str:
        return f"SELECT quantum_account.portfolio_id, quantum_account.name, quantum_account.starting_balance, quantum_account.account_id \nFROM quantum_account JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_account.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_account.account_id = {account_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_account_found(
        self,
        user: User,
        account_id: int,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Any,
    ) -> None:
        response = await account.delete_account(
            account_id=account_id, db=mock_db, current_user=user
        )

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
            await account.delete_account(
                account_id=account_id, db=mock_db, current_user=user
            )

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
        return Account.model_validate(
            complete_account.model_dump(), update={"name": "some new name"}
        )

    @pytest.fixture
    def expected_response(
        self, updated_account: Account, starting_balance: int
    ) -> AccountRead:
        return AccountRead.model_validate(
            updated_account.model_dump(),
            update={"starting_balance": starting_balance, "balance": starting_balance},
        )

    @pytest.mark.parametrize(
        "db_one_or_none_return_val", [lazy_fixture("complete_account")]
    )
    @patch("miapeer.routers.quantum.account.get_account_balance")
    async def test_update_with_account_found(
        self,
        patched_get_account_balance: Mock,
        user: User,
        account_id: int,
        account_updates: AccountUpdate,
        mock_db: Mock,
        expected_sql: str,
        updated_account: Account,
        expected_response: AccountRead,
        starting_balance: int,
    ) -> None:
        patched_get_account_balance.return_value = starting_balance

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
