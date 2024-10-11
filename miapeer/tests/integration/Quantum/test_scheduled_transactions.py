from datetime import date
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.scheduled_transaction import ScheduledTransaction
from miapeer.models.quantum.transaction_type import TransactionType


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_scheduled_transactions_in_account(
        self,
        client: TestClient,
        my_account_1: Account,
        my_minimal_scheduled_transaction: ScheduledTransaction,
        my_scheduled_transaction: ScheduledTransaction,
    ) -> None:
        response = client.get(
            f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions",
        )

        expected = [
            {
                "scheduled_transaction_id": my_minimal_scheduled_transaction.scheduled_transaction_id,
                "account_id": my_minimal_scheduled_transaction.account_id,
                "transaction_type_id": my_minimal_scheduled_transaction.transaction_type_id,
                "payee_id": my_minimal_scheduled_transaction.payee_id,
                "category_id": my_minimal_scheduled_transaction.category_id,
                "fixed_amount": my_minimal_scheduled_transaction.fixed_amount,
                "estimate_occurrences": my_minimal_scheduled_transaction.estimate_occurrences,
                "prompt_days": my_minimal_scheduled_transaction.prompt_days,
                "start_date": my_minimal_scheduled_transaction.start_date.strftime("%Y-%m-%d"),
                "end_date": None,
                "limit_occurrences": my_minimal_scheduled_transaction.limit_occurrences,
                "repeat_option_id": my_minimal_scheduled_transaction.repeat_option_id,
                "notes": my_minimal_scheduled_transaction.notes,
                "on_autopay": my_minimal_scheduled_transaction.on_autopay,
                "next_transaction": {
                    "transaction_type_id": my_minimal_scheduled_transaction.transaction_type_id,
                    "payee_id": my_minimal_scheduled_transaction.payee_id,
                    "category_id": my_minimal_scheduled_transaction.category_id,
                    "amount": my_minimal_scheduled_transaction.fixed_amount,
                    "transaction_date": my_minimal_scheduled_transaction.start_date.strftime("%Y-%m-%d"),
                    "clear_date": None,
                    "check_number": None,
                    "exclude_from_forecast": False,
                    "notes": my_minimal_scheduled_transaction.notes,
                    "transaction_id": 0,
                    "account_id": my_minimal_scheduled_transaction.account_id,
                    "balance": None,
                },
            },
            {
                "scheduled_transaction_id": my_scheduled_transaction.scheduled_transaction_id,
                "account_id": my_scheduled_transaction.account_id,
                "transaction_type_id": my_scheduled_transaction.transaction_type_id,
                "payee_id": my_scheduled_transaction.payee_id,
                "category_id": my_scheduled_transaction.category_id,
                "fixed_amount": my_scheduled_transaction.fixed_amount,
                "estimate_occurrences": my_scheduled_transaction.estimate_occurrences,
                "prompt_days": my_scheduled_transaction.prompt_days,
                "start_date": my_scheduled_transaction.start_date.strftime("%Y-%m-%d"),
                "end_date": my_scheduled_transaction.end_date.strftime("%Y-%m-%d") if my_scheduled_transaction.end_date is not None else None,
                "limit_occurrences": my_scheduled_transaction.limit_occurrences,
                "repeat_option_id": my_scheduled_transaction.repeat_option_id,
                "notes": my_scheduled_transaction.notes,
                "on_autopay": my_scheduled_transaction.on_autopay,
                "next_transaction": {
                    "transaction_type_id": my_scheduled_transaction.transaction_type_id,
                    "payee_id": my_scheduled_transaction.payee_id,
                    "category_id": my_scheduled_transaction.category_id,
                    "amount": my_scheduled_transaction.fixed_amount,
                    "transaction_date": my_scheduled_transaction.start_date.strftime("%Y-%m-%d"),
                    "clear_date": None,
                    "check_number": None,
                    "exclude_from_forecast": False,
                    "notes": my_scheduled_transaction.notes,
                    "transaction_id": 0,
                    "account_id": my_scheduled_transaction.account_id,
                    "balance": None,
                },
            },
        ]

        actual = response.json()

        assert response.status_code == 200
        assert actual == expected


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    @pytest.mark.parametrize(
        "account, transaction_type, payee, category, fixed_amount, estimate_occurrences, prompt_days, start_date, end_date, limit_occurrences, repeat_option_id, notes, on_autopay",
        [
            (
                pytest.lazy_fixture("my_account_1"),
                None,
                None,
                None,
                None,
                None,
                None,
                "2001-02-03",
                None,
                None,
                False,
                None,
                False,
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                2233,
                3,
                7,
                "2001-02-03",
                "2004-03-02",
                13,
                1,
                "Some scheduled transaction note",
                False,
            ),
            (
                pytest.lazy_fixture("my_account_2"),
                pytest.lazy_fixture("my_transaction_type_1"),
                pytest.lazy_fixture("my_payee_2"),
                pytest.lazy_fixture("my_category_1"),
                2468,
                None,
                None,
                "2003-02-01",
                None,
                20,
                None,
                "Some cool notes",
                True,
            ),
        ],
    )
    def test_create_scheduled_transaction_succeeds(
        self,
        client: TestClient,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: str,
        end_date: Optional[str],
        limit_occurrences: Optional[str],
        repeat_option_id: int,
        notes: Optional[str],
        on_autopay: bool,
        not_my_scheduled_transaction: ScheduledTransaction,
    ) -> None:
        response = client.post(
            f"/quantum/v1/accounts/{account.account_id}/scheduled-transactions",
            json={
                "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
                "payee_id": getattr(payee, "payee_id", None),
                "category_id": getattr(category, "category_id", None),
                "fixed_amount": fixed_amount,
                "estimate_occurrences": estimate_occurrences,
                "prompt_days": prompt_days,
                "start_date": start_date,
                "end_date": end_date,
                "limit_occurrences": limit_occurrences,
                "repeat_option_id": repeat_option_id,
                "notes": notes,
                "on_autopay": on_autopay,
            },
        )

        scheduled_transaction_id = 0
        if not_my_scheduled_transaction.scheduled_transaction_id is not None:
            scheduled_transaction_id = not_my_scheduled_transaction.scheduled_transaction_id

        actual = response.json()

        expected = {
            "account_id": account.account_id,
            "scheduled_transaction_id": (scheduled_transaction_id + 1),  # Increment by 1, the last scheduled transaction ID inserted
            "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
            "payee_id": getattr(payee, "payee_id", None),
            "category_id": getattr(category, "category_id", None),
            "fixed_amount": fixed_amount,
            "estimate_occurrences": estimate_occurrences,
            "prompt_days": prompt_days,
            "start_date": start_date,
            "end_date": end_date,
            "limit_occurrences": limit_occurrences,
            "repeat_option_id": repeat_option_id,
            "notes": notes,
            "on_autopay": on_autopay,
            "next_transaction": None,
        }

        assert response.status_code == 200
        assert actual == expected

    @pytest.mark.parametrize(
        "account, transaction_type, payee, category, fixed_amount, estimate_occurrences, prompt_days, start_date, end_date, limit_occurrences, repeat_option_id, notes, on_autopay, expected_response",
        [
            (
                pytest.lazy_fixture("not_my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                None,
                None,
                "2001-02-03",
                None,
                None,
                1,
                "Someone else's account",
                False,
                {"detail": "Account not found"},
            ),
            (
                Account(portfolio_id=0, account_id=999999, name="", starting_balance=0),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                None,
                None,
                "2001-02-03",
                None,
                None,
                1,
                "Account doesn't exist",
                False,
                {"detail": "Account not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("not_my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                None,
                None,
                "2001-02-03",
                None,
                None,
                1,
                "Someone else's transaction type",
                False,
                {"detail": "Transaction type not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("not_my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                None,
                None,
                "2001-02-03",
                None,
                None,
                1,
                "Someone else's payee",
                False,
                {"detail": "Payee not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("not_my_category_2"),
                111,
                None,
                None,
                "2001-02-03",
                None,
                None,
                1,
                "Someone else's category",
                False,
                {"detail": "Category not found"},
            ),
        ],
    )
    def test_create_scheduled_transaction_fails(
        self,
        client: TestClient,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: str,
        end_date: Optional[str],
        limit_occurrences: Optional[int],
        repeat_option_id: int,
        notes: Optional[str],
        on_autopay: bool,
        expected_response: dict[str, str],
    ) -> None:
        response = client.post(
            f"/quantum/v1/accounts/{account.account_id}/scheduled-transactions",
            json={
                "transaction_type_id": transaction_type.transaction_type_id,
                "payee_id": payee.payee_id,
                "category_id": category.category_id,
                "fixed_amount": fixed_amount,
                "estimate_occurrences": estimate_occurrences,
                "prompt_days": prompt_days,
                "start_date": start_date,
                "end_date": end_date,
                "limit_occurrences": limit_occurrences,
                "repeat_option_id": repeat_option_id,
                "notes": notes,
                "on_autopay": on_autopay,
            },
        )

        assert response.status_code == 404
        assert response.json() == expected_response


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_scheduled_transaction_in_portfolio_succeeds(self, client: TestClient, my_scheduled_transaction: ScheduledTransaction) -> None:
        response = client.get(
            f"/quantum/v1/accounts/{my_scheduled_transaction.account_id}/scheduled-transactions/{my_scheduled_transaction.scheduled_transaction_id}"
        )

        expected = {
            "account_id": my_scheduled_transaction.account_id,
            "scheduled_transaction_id": my_scheduled_transaction.scheduled_transaction_id,
            "transaction_type_id": getattr(my_scheduled_transaction, "transaction_type_id", None),
            "payee_id": getattr(my_scheduled_transaction, "payee_id", None),
            "category_id": getattr(my_scheduled_transaction, "category_id", None),
            "fixed_amount": my_scheduled_transaction.fixed_amount,
            "estimate_occurrences": my_scheduled_transaction.estimate_occurrences,
            "prompt_days": my_scheduled_transaction.prompt_days,
            "start_date": my_scheduled_transaction.start_date.strftime("%Y-%m-%d"),
            "end_date": my_scheduled_transaction.end_date.strftime("%Y-%m-%d") if my_scheduled_transaction.end_date is not None else None,
            "limit_occurrences": my_scheduled_transaction.limit_occurrences,
            "repeat_option_id": my_scheduled_transaction.repeat_option_id,
            "notes": my_scheduled_transaction.notes,
            "on_autopay": my_scheduled_transaction.on_autopay,
            "next_transaction": {
                "transaction_type_id": getattr(my_scheduled_transaction, "transaction_type_id", None),
                "payee_id": getattr(my_scheduled_transaction, "payee_id", None),
                "category_id": getattr(my_scheduled_transaction, "category_id", None),
                "amount": my_scheduled_transaction.fixed_amount,
                "transaction_date": date.today().strftime("%Y-%m-%d"),
                "clear_date": None,
                "check_number": None,
                "exclude_from_forecast": False,
                "notes": my_scheduled_transaction.notes,
                "transaction_id": 0,
                "account_id": my_scheduled_transaction.account_id,
                "balance": None,
            },
        }

        actual = response.json()

        assert response.status_code == 200
        assert actual == expected

    def test_get_one_scheduled_transaction_in_wrong_portfolio_fails(
        self, client: TestClient, my_account_1: Account, not_my_scheduled_transaction: ScheduledTransaction
    ) -> None:
        response = client.get(
            f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions/{not_my_scheduled_transaction.scheduled_transaction_id}"
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}

    @pytest.mark.parametrize("scheduled_transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_get_one_scheduled_transaction_with_invalid_scheduled_transaction_id_fails(
        self, client: TestClient, my_account_1: Account, scheduled_transaction_id: int
    ) -> None:
        response = client.get(f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions/{scheduled_transaction_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    @pytest.mark.parametrize(
        "scheduled_transaction, account, transaction_type, payee, category, fixed_amount, estimate_occurrences, prompt_days, start_date, end_date, limit_occurrences, repeat_option_id, notes, on_autopay",
        [
            (
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("my_account_2"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                38438,
                933,
                38,
                date(year=2021, month=2, day=3),
                date(year=2020, month=1, day=2),
                8129,
                2,
                "new note",
                False,
            ),
            (
                pytest.lazy_fixture("my_scheduled_transaction"),
                None,
                None,
                None,
                None,
                0,
                None,
                None,
                date(year=2128, month=7, day=6),
                None,
                None,
                None,
                None,
                True,
            ),
        ],
    )
    def test_update_scheduled_transaction_succeeds(
        self,
        client: TestClient,
        scheduled_transaction: ScheduledTransaction,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: date,
        end_date: Optional[date],
        limit_occurrences: int,
        repeat_option_id: int,
        notes: str,
        on_autopay: bool,
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{scheduled_transaction.account_id}/scheduled-transactions/{scheduled_transaction.scheduled_transaction_id}",
            json={
                "account_id": getattr(account, "account_id", None),
                "scheduled_transaction_id": scheduled_transaction.scheduled_transaction_id,
                "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
                "payee_id": getattr(payee, "payee_id", None),
                "category_id": getattr(category, "category_id", None),
                "fixed_amount": fixed_amount,
                "estimate_occurrences": estimate_occurrences,
                "prompt_days": prompt_days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d") if end_date is not None else None,
                "limit_occurrences": limit_occurrences,
                "repeat_option_id": repeat_option_id,
                "notes": notes,
                "on_autopay": on_autopay,
            },
        )

        assert response.status_code == 200

        expected = {
            # Trying to change the account_id isn't allowed
            "account_id": scheduled_transaction.account_id,
            "scheduled_transaction_id": scheduled_transaction.scheduled_transaction_id,
            "transaction_type_id": getattr(scheduled_transaction, "transaction_type_id", None),
            "payee_id": getattr(payee, "payee_id", None),
            "category_id": getattr(category, "category_id", None),
            "fixed_amount": fixed_amount,
            "estimate_occurrences": estimate_occurrences,
            "prompt_days": prompt_days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d") if end_date is not None else None,
            "limit_occurrences": limit_occurrences,
            "repeat_option_id": repeat_option_id,
            "notes": notes,
            "on_autopay": on_autopay,
            "next_transaction": {
                "transaction_type_id": getattr(scheduled_transaction, "transaction_type_id", None),
                "payee_id": getattr(payee, "payee_id", None),
                "category_id": getattr(category, "category_id", None),
                "amount": fixed_amount,
                "transaction_date": start_date.strftime("%Y-%m-%d"),
                "clear_date": None,
                "check_number": None,
                "exclude_from_forecast": False,
                "notes": notes,
                "transaction_id": 0,
                "account_id": scheduled_transaction.account_id,
                "balance": None,
            },
        }

        actual = response.json()

        assert actual == expected

    def test_update_someone_elses_scheduled_transaction_fails(
        self, client: TestClient, my_account_1: Account, not_my_scheduled_transaction: ScheduledTransaction
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{my_account_1. account_id}/scheduled-transactions/{not_my_scheduled_transaction.scheduled_transaction_id}",
            json={"fixed_amount": 0, "start_date": "2000-01-01", "on_autopay": False},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}

    @pytest.mark.parametrize("scheduled_transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_update_transaction_with_invalid_scheduled_transaction_id_fails(
        self, client: TestClient, my_account_1: Account, scheduled_transaction_id: int
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions/{scheduled_transaction_id}",
            json={"fixed_amount": 0, "start_date": "2000-01-01", "on_autopay": False},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}

    @pytest.mark.parametrize(
        "account, scheduled_transaction, transaction_type, payee, category, fixed_amount, estimate_occurrences, prompt_days, start_date, end_date, limit_occurrences, repeat_option_id, notes, on_autopay, expected_response",
        [
            (
                pytest.lazy_fixture("not_my_account_1"),
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                3,
                7,
                "2001-02-03",
                None,
                10,
                1,
                "Someone else's account",
                False,
                {"detail": "Scheduled transaction not found"},
            ),
            (
                Account(portfolio_id=0, account_id=999999, name="", starting_balance=0),
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                3,
                7,
                "2001-02-03",
                None,
                10,
                1,
                "Account doesn't exist",
                False,
                {"detail": "Scheduled transaction not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("not_my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                3,
                7,
                "2001-02-03",
                None,
                10,
                1,
                "Someone else's transaction type",
                False,
                {"detail": "Transaction type not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("not_my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                3,
                7,
                "2001-02-03",
                None,
                10,
                1,
                "Someone else's payee",
                False,
                {"detail": "Payee not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_scheduled_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("not_my_category_2"),
                111,
                3,
                7,
                "2001-02-03",
                None,
                10,
                1,
                "Someone else's category",
                False,
                {"detail": "Category not found"},
            ),
        ],
    )
    def test_update_scheduled_transaction_with_bad_data_fails(
        self,
        client: TestClient,
        account: Account,
        scheduled_transaction: ScheduledTransaction,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        fixed_amount: int,
        estimate_occurrences: int,
        prompt_days: int,
        start_date: str,
        end_date: Optional[str],
        limit_occurrences: Optional[int],
        repeat_option_id: bool,
        notes: Optional[str],
        on_autopay: bool,
        expected_response: dict[str, str],
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{account.account_id}/scheduled-transactions/{scheduled_transaction.scheduled_transaction_id}",
            json={
                "transaction_type_id": transaction_type.transaction_type_id,
                "payee_id": payee.payee_id,
                "category_id": category.category_id,
                "fixed_amount": fixed_amount,
                "estimate_occurrences": estimate_occurrences,
                "prompt_days": prompt_days,
                "start_date": start_date,
                "end_date": end_date,
                "limit_occurrences": limit_occurrences,
                "repeat_option_id": repeat_option_id,
                "notes": notes,
                "on_autopay": on_autopay,
            },
        )

        assert response.status_code == 404
        assert response.json() == expected_response


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_scheduled_transaction_succeeds(self, client: TestClient, my_scheduled_transaction: ScheduledTransaction) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{my_scheduled_transaction.account_id}/scheduled-transactions/{my_scheduled_transaction.scheduled_transaction_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_scheduled_transaction_in_wrong_portfolio_fails(
        self, client: TestClient, not_my_account_1: Account, my_scheduled_transaction: ScheduledTransaction
    ) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{not_my_account_1.account_id}/scheduled-transactions/{my_scheduled_transaction.scheduled_transaction_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}

    def test_delete_someone_elses_scheduled_transaction_fails(
        self, client: TestClient, my_account_1: Account, not_my_scheduled_transaction: ScheduledTransaction
    ) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions/{not_my_scheduled_transaction.scheduled_transaction_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}

    @pytest.mark.parametrize("scheduled_transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_delete_transaction_with_invalid_scheduled_transaction_id_fails(
        self, client: TestClient, my_account_1: Account, scheduled_transaction_id: int
    ) -> None:
        response = client.delete(f"/quantum/v1/accounts/{my_account_1.account_id}/scheduled-transactions/{scheduled_transaction_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Scheduled transaction not found"}
