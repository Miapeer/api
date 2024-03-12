import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.transaction_type import TransactionType


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_transaction_types_in_portfolio(
        self, client: TestClient, my_transaction_type_1: TransactionType, my_transaction_type_2: TransactionType
    ) -> None:
        response = client.get(
            "/quantum/v1/transaction-types",
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "portfolio_id": my_transaction_type_1.portfolio_id,
                "transaction_type_id": my_transaction_type_1.transaction_type_id,
                "name": my_transaction_type_1.name,
            },
            {
                "portfolio_id": my_transaction_type_2.portfolio_id,
                "transaction_type_id": my_transaction_type_2.transaction_type_id,
                "name": my_transaction_type_2.name,
            },
        ]


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    def test_create_transaction_type(
        self, client: TestClient, my_portfolio: Portfolio, not_my_transaction_type_2: TransactionType
    ) -> None:
        response = client.post(
            "/quantum/v1/transaction-types",
            json={"portfolio_id": my_portfolio.portfolio_id, "name": "Pie Throwing"},
        )

        transaction_type_id = 0
        if not_my_transaction_type_2.transaction_type_id is not None:
            transaction_type_id = not_my_transaction_type_2.transaction_type_id

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_portfolio.portfolio_id,
            "transaction_type_id": (transaction_type_id + 1),  # Increment by 1, the last account ID inserted
            "name": "Pie Throwing",
        }


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_transaction_type_in_portfolio_succeeds(
        self, client: TestClient, my_transaction_type_1: TransactionType
    ) -> None:
        response = client.get(f"/quantum/v1/transaction-types/{my_transaction_type_1.transaction_type_id}")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_transaction_type_1.portfolio_id,
            "transaction_type_id": my_transaction_type_1.transaction_type_id,
            "name": my_transaction_type_1.name,
        }

    def test_get_one_transaction_type_in_wrong_portfolio_fails(
        self, client: TestClient, not_my_transaction_type_1: TransactionType
    ) -> None:
        response = client.get(f"/quantum/v1/transaction-types/{not_my_transaction_type_1.transaction_type_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}

    @pytest.mark.parametrize("transaction_type_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_get_one_transaction_type_with_invalid_transaction_type_id_fails(
        self, client: TestClient, transaction_type_id: int
    ) -> None:
        response = client.get(f"/quantum/v1/transaction-types/{transaction_type_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    def test_update_transaction_type_succeeds(
        self, client: TestClient, my_transaction_type_1: TransactionType
    ) -> None:
        response = client.patch(
            f"/quantum/v1/transaction-types/{my_transaction_type_1.transaction_type_id}",
            json={"name": "Pie Throwing"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_transaction_type_1.portfolio_id,
            "transaction_type_id": my_transaction_type_1.transaction_type_id,
            "name": "Pie Throwing",
        }

    def test_update_transaction_type_in_wrong_portfolio_fails(
        self, client: TestClient, not_my_transaction_type_1: TransactionType
    ) -> None:
        response = client.patch(
            f"/quantum/v1/transaction-types/{not_my_transaction_type_1.transaction_type_id}",
            json={"name": "Pie Throwing"},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}

    @pytest.mark.parametrize("transaction_type_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_update_transaction_type_with_invalid_transaction_type_id_fails(
        self, client: TestClient, transaction_type_id: int
    ) -> None:
        response = client.patch(f"/quantum/v1/transaction-types/{transaction_type_id}", json={"name": "Pie Throwing"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_transaction_type_succeeds(
        self, client: TestClient, my_transaction_type_1: TransactionType
    ) -> None:
        response = client.delete(
            f"/quantum/v1/transaction-types/{my_transaction_type_1.transaction_type_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_transaction_type_in_wrong_portfolio_fails(
        self, client: TestClient, not_my_transaction_type_1: TransactionType
    ) -> None:
        response = client.delete(
            f"/quantum/v1/transaction-types/{not_my_transaction_type_1.transaction_type_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}

    @pytest.mark.parametrize("transaction_type_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_delete_transaction_type_with_invalid_transaction_type_id_fails(
        self, client: TestClient, transaction_type_id: int
    ) -> None:
        response = client.delete(f"/quantum/v1/transaction-types/{transaction_type_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Transaction type not found"}
