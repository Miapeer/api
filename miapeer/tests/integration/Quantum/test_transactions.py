from datetime import date
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.transaction import Transaction
from miapeer.models.quantum.transaction_type import TransactionType


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_transactions_in_account(
        self,
        client: TestClient,
        my_account_1: Account,
        my_minimal_transaction: Transaction,
        my_debit_transaction: Transaction,
        my_credit_transaction: Transaction,
    ) -> None:
        response = client.get(
            f"/quantum/v1/accounts/{my_account_1.account_id}/transactions",
        )

        assert response.status_code == 200

        expected = [
            {
                "account_id": my_minimal_transaction.account_id,
                "transaction_id": my_minimal_transaction.transaction_id,
                "transaction_type_id": None,
                "payee_id": None,
                "category_id": None,
                "amount": my_minimal_transaction.amount,
                "transaction_date": my_minimal_transaction.transaction_date.strftime("%Y-%m-%d"),
                "clear_date": None,
                "check_number": None,
                "exclude_from_forecast": my_minimal_transaction.exclude_from_forecast,
                "notes": None,
                "balance": my_account_1.starting_balance + my_minimal_transaction.amount,
            },
            {
                "account_id": my_debit_transaction.account_id,
                "transaction_id": my_debit_transaction.transaction_id,
                "transaction_type_id": my_debit_transaction.transaction_type_id,
                "payee_id": my_debit_transaction.payee_id,
                "category_id": my_debit_transaction.category_id,
                "amount": my_debit_transaction.amount,
                "transaction_date": my_debit_transaction.transaction_date.strftime("%Y-%m-%d"),
                "clear_date": my_debit_transaction.clear_date.strftime("%Y-%m-%d") if my_debit_transaction.clear_date is not None else None,
                "check_number": my_debit_transaction.check_number,
                "exclude_from_forecast": my_debit_transaction.exclude_from_forecast,
                "notes": my_debit_transaction.notes,
                "balance": my_account_1.starting_balance + my_minimal_transaction.amount + my_debit_transaction.amount,
            },
            {
                "account_id": my_credit_transaction.account_id,
                "transaction_id": my_credit_transaction.transaction_id,
                "transaction_type_id": my_credit_transaction.transaction_type_id,
                "payee_id": my_credit_transaction.payee_id,
                "category_id": my_credit_transaction.category_id,
                "amount": my_credit_transaction.amount,
                "transaction_date": my_credit_transaction.transaction_date.strftime("%Y-%m-%d"),
                "clear_date": None,
                "check_number": my_credit_transaction.check_number,
                "exclude_from_forecast": my_credit_transaction.exclude_from_forecast,
                "notes": my_credit_transaction.notes,
                "balance": my_account_1.starting_balance + my_minimal_transaction.amount + my_debit_transaction.amount + my_credit_transaction.amount,
            },
        ]

        actual = response.json()

        assert actual == expected


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    @pytest.mark.parametrize(
        "account, transaction_type, payee, category, amount, transaction_date, clear_date, check_number, exclude_from_forecast, notes",
        [
            (
                pytest.lazy_fixture("my_account_1"),
                None,
                None,
                None,
                0,
                "2001-02-03",
                None,
                None,
                False,
                None,
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                2233,
                "2001-02-03",
                None,
                None,
                False,
                None,
            ),
            (
                pytest.lazy_fixture("my_account_2"),
                pytest.lazy_fixture("my_transaction_type_1"),
                pytest.lazy_fixture("my_payee_2"),
                pytest.lazy_fixture("my_category_1"),
                2468,
                "2003-02-01",
                "2004-12-31",
                "my check num",
                True,
                "Some cool notes",
            ),
        ],
    )
    def test_create_transaction_succeeds(
        self,
        client: TestClient,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        amount: int,
        transaction_date: str,
        clear_date: Optional[str],
        check_number: Optional[str],
        exclude_from_forecast: bool,
        notes: Optional[str],
        not_my_credit_transaction: Transaction,
    ) -> None:
        response = client.post(
            f"/quantum/v1/accounts/{account.account_id}/transactions",
            json={
                "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
                "payee_id": getattr(payee, "payee_id", None),
                "category_id": getattr(category, "category_id", None),
                "amount": amount,
                "transaction_date": transaction_date,
                "clear_date": clear_date,
                "check_number": check_number,
                "exclude_from_forecast": exclude_from_forecast,
                "notes": notes,
            },
        )

        transaction_id = 0
        if not_my_credit_transaction.transaction_id is not None:
            transaction_id = not_my_credit_transaction.transaction_id

        assert response.status_code == 200
        assert response.json() == {
            "account_id": account.account_id,
            "transaction_id": (transaction_id + 1),  # Increment by 1, the last transaction ID inserted
            "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
            "payee_id": getattr(payee, "payee_id", None),
            "category_id": getattr(category, "category_id", None),
            "amount": amount,
            "transaction_date": transaction_date,
            "clear_date": clear_date,
            "check_number": check_number,
            "exclude_from_forecast": exclude_from_forecast,
            "notes": notes,
            "balance": None,
        }

    @pytest.mark.parametrize(
        "account, transaction_type, payee, category, amount, transaction_date, clear_date, check_number, exclude_from_forecast, notes, expected_response",
        [
            (
                pytest.lazy_fixture("not_my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's account",
                {"detail": "Account not found"},
            ),
            (
                Account(portfolio_id=0, account_id=999999, name="", starting_balance=0),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Account doesn't exist",
                {"detail": "Account not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("not_my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's transaction type",
                {"detail": "Transaction type not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("not_my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's payee",
                {"detail": "Payee not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("not_my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's category",
                {"detail": "Category not found"},
            ),
        ],
    )
    def test_create_transaction_fails(
        self,
        client: TestClient,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        amount: int,
        transaction_date: str,
        clear_date: Optional[str],
        check_number: Optional[str],
        exclude_from_forecast: bool,
        notes: Optional[str],
        expected_response: dict[str, str],
    ) -> None:
        response = client.post(
            f"/quantum/v1/accounts/{account.account_id}/transactions",
            json={
                "transaction_type_id": transaction_type.transaction_type_id,
                "payee_id": payee.payee_id,
                "category_id": category.category_id,
                "amount": amount,
                "transaction_date": transaction_date,
                "clear_date": clear_date,
                "check_number": check_number,
                "exclude_from_forecast": exclude_from_forecast,
                "notes": notes,
            },
        )

        assert response.status_code == 404
        assert response.json() == expected_response


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_transaction_in_portfolio_succeeds(self, client: TestClient, my_debit_transaction: Transaction) -> None:
        response = client.get(f"/quantum/v1/accounts/{my_debit_transaction.account_id}/transactions/{my_debit_transaction.transaction_id}")

        assert response.status_code == 200
        assert response.json() == {
            "account_id": my_debit_transaction.account_id,
            "transaction_id": my_debit_transaction.transaction_id,
            "transaction_type_id": getattr(my_debit_transaction, "transaction_type_id", None),
            "payee_id": getattr(my_debit_transaction, "payee_id", None),
            "category_id": getattr(my_debit_transaction, "category_id", None),
            "amount": my_debit_transaction.amount,
            "transaction_date": my_debit_transaction.transaction_date.strftime("%Y-%m-%d"),
            "clear_date": my_debit_transaction.clear_date.strftime("%Y-%m-%d") if my_debit_transaction.clear_date is not None else None,
            "check_number": my_debit_transaction.check_number,
            "exclude_from_forecast": my_debit_transaction.exclude_from_forecast,
            "notes": my_debit_transaction.notes,
            "balance": None,
        }

    def test_get_one_transaction_in_wrong_portfolio_fails(
        self, client: TestClient, my_account_1: Account, not_my_debit_transaction: Transaction
    ) -> None:
        response = client.get(f"/quantum/v1/accounts/{my_account_1.account_id}/transactions/{not_my_debit_transaction.transaction_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}

    @pytest.mark.parametrize("transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_get_one_transaction_with_invalid_transaction_id_fails(self, client: TestClient, my_account_1: Account, transaction_id: int) -> None:
        response = client.get(f"/quantum/v1/accounts/{my_account_1.account_id}/transactions/{transaction_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    @pytest.mark.parametrize(
        "transaction, account, transaction_type, payee, category, amount, transaction_date, clear_date, check_number, exclude_from_forecast, notes",
        [
            (
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("my_account_2"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                38438,
                date(year=2021, month=2, day=3),
                date(year=2020, month=1, day=2),
                "ck 1",
                False,
                "new note",
            ),
            (
                pytest.lazy_fixture("my_debit_transaction"),
                None,
                None,
                None,
                None,
                0,
                date(year=2128, month=7, day=6),
                None,
                None,
                False,
                None,
            ),
        ],
    )
    def test_update_transaction_succeeds(
        self,
        client: TestClient,
        transaction: Transaction,
        account: Account,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        amount: int,
        transaction_date: date,
        clear_date: Optional[date],
        check_number: str,
        exclude_from_forecast: bool,
        notes: str,
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{transaction.account_id}/transactions/{transaction.transaction_id}",
            json={
                "account_id": getattr(account, "account_id", None),
                "transaction_id": transaction.transaction_id,
                "transaction_type_id": getattr(transaction_type, "transaction_type_id", None),
                "payee_id": getattr(payee, "payee_id", None),
                "category_id": getattr(category, "category_id", None),
                "amount": amount,
                "transaction_date": transaction_date.strftime("%Y-%m-%d"),
                "clear_date": clear_date.strftime("%Y-%m-%d") if clear_date is not None else None,
                "check_number": check_number,
                "exclude_from_forecast": exclude_from_forecast,
                "notes": notes,
            },
        )

        expected_response = {
            # Trying to change the account_id isn't allowed
            "account_id": transaction.account_id,
            "transaction_id": transaction.transaction_id,
            "transaction_type_id": getattr(transaction, "transaction_type_id", None),
            "payee_id": getattr(payee, "payee_id", None),
            "category_id": getattr(category, "category_id", None),
            "amount": amount,
            "transaction_date": transaction_date.strftime("%Y-%m-%d"),
            "clear_date": clear_date.strftime("%Y-%m-%d") if clear_date is not None else None,
            "check_number": check_number,
            "exclude_from_forecast": exclude_from_forecast,
            "notes": notes,
            "balance": None,
        }

        assert response.status_code == 200
        assert response.json() == expected_response

    def test_update_someone_elses_transaction_fails(self, client: TestClient, my_account_1: Account, not_my_debit_transaction: Transaction) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{my_account_1. account_id}/transactions/{not_my_debit_transaction.transaction_id}",
            json={"amount": 0, "transaction_date": "2000-01-01", "exclude_from_forecast": False},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}

    @pytest.mark.parametrize("transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_update_transaction_with_invalid_transaction_id_fails(self, client: TestClient, my_account_1: Account, transaction_id: int) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{my_account_1.account_id}/transactions/{transaction_id}",
            json={"amount": 0, "transaction_date": "2000-01-01", "exclude_from_forecast": False},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}

    @pytest.mark.parametrize(
        "account, transaction, transaction_type, payee, category, amount, transaction_date, clear_date, check_number, exclude_from_forecast, notes, expected_response",
        [
            (
                pytest.lazy_fixture("not_my_account_1"),
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's account",
                {"detail": "Transaction not found"},
            ),
            (
                Account(portfolio_id=0, account_id=999999, name="", starting_balance=0),
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Account doesn't exist",
                {"detail": "Transaction not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("not_my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's transaction type",
                {"detail": "Transaction type not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("not_my_payee_1"),
                pytest.lazy_fixture("my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's payee",
                {"detail": "Payee not found"},
            ),
            (
                pytest.lazy_fixture("my_account_1"),
                pytest.lazy_fixture("my_debit_transaction"),
                pytest.lazy_fixture("my_transaction_type_2"),
                pytest.lazy_fixture("my_payee_1"),
                pytest.lazy_fixture("not_my_category_2"),
                111,
                "2001-02-03",
                None,
                None,
                False,
                "Someone else's category",
                {"detail": "Category not found"},
            ),
        ],
    )
    def test_update_transaction_with_bad_data_fails(
        self,
        client: TestClient,
        account: Account,
        transaction: Transaction,
        transaction_type: TransactionType,
        payee: Payee,
        category: Category,
        amount: int,
        transaction_date: str,
        clear_date: Optional[str],
        check_number: Optional[str],
        exclude_from_forecast: bool,
        notes: Optional[str],
        expected_response: dict[str, str],
    ) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{account.account_id}/transactions/{transaction.transaction_id}",
            json={
                "transaction_type_id": transaction_type.transaction_type_id,
                "payee_id": payee.payee_id,
                "category_id": category.category_id,
                "amount": amount,
                "transaction_date": transaction_date,
                "clear_date": clear_date,
                "check_number": check_number,
                "exclude_from_forecast": exclude_from_forecast,
                "notes": notes,
            },
        )

        assert response.status_code == 404
        assert response.json() == expected_response


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_transaction_succeeds(self, client: TestClient, my_debit_transaction: Transaction) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{my_debit_transaction.account_id}/transactions/{my_debit_transaction.transaction_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_transaction_in_wrong_portfolio_fails(
        self, client: TestClient, not_my_account_1: Account, my_debit_transaction: Transaction
    ) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{not_my_account_1.account_id}/transactions/{my_debit_transaction.transaction_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}

    def test_delete_someone_elses_transaction_fails(self, client: TestClient, my_account_1: Account, not_my_debit_transaction: Transaction) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{my_account_1.account_id}/transactions/{not_my_debit_transaction.transaction_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}

    @pytest.mark.parametrize("transaction_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_delete_transaction_with_invalid_transaction_id_fails(self, client: TestClient, my_account_1: Account, transaction_id: int) -> None:
        response = client.delete(f"/quantum/v1/accounts/{my_account_1.account_id}/transactions/{transaction_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction not found"}
