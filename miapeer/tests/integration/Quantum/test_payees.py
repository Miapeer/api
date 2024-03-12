import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.portfolio import Portfolio


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_payees_in_portfolio(self, client: TestClient, my_payee_1: Payee, my_payee_2: Payee) -> None:
        response = client.get(
            "/quantum/v1/payees",
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "portfolio_id": my_payee_1.portfolio_id,
                "payee_id": my_payee_1.payee_id,
                "name": my_payee_1.name,
            },
            {
                "portfolio_id": my_payee_2.portfolio_id,
                "payee_id": my_payee_2.payee_id,
                "name": my_payee_2.name,
            },
        ]


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    def test_create_payee(self, client: TestClient, my_portfolio: Portfolio, not_my_payee_2: Payee) -> None:
        response = client.post(
            "/quantum/v1/payees",
            json={"portfolio_id": my_portfolio.portfolio_id, "name": "godzilla"},
        )

        payee_id = 0
        if not_my_payee_2.payee_id is not None:
            payee_id = not_my_payee_2.payee_id

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_portfolio.portfolio_id,
            "payee_id": (payee_id + 1),  # Increment by 1, the last account ID inserted
            "name": "godzilla",
        }


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_payee_in_portfolio_succeeds(self, client: TestClient, my_payee_1: Payee) -> None:
        response = client.get(f"/quantum/v1/payees/{my_payee_1.payee_id}")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_payee_1.portfolio_id,
            "payee_id": my_payee_1.payee_id,
            "name": my_payee_1.name,
        }

    def test_get_one_payee_in_wrong_portfolio_fails(self, client: TestClient, not_my_payee_1: Payee) -> None:
        response = client.get(f"/quantum/v1/payees/{not_my_payee_1.payee_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}

    @pytest.mark.parametrize("payee_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_get_one_payee_with_invalid_payee_id_fails(self, client: TestClient, payee_id: int) -> None:
        response = client.get(f"/quantum/v1/payees/{payee_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    def test_update_payee_succeeds(self, client: TestClient, my_payee_1: Payee) -> None:
        response = client.patch(
            f"/quantum/v1/payees/{my_payee_1.payee_id}",
            json={"name": "Coffee"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_payee_1.portfolio_id,
            "payee_id": my_payee_1.payee_id,
            "name": "Coffee",
        }

    def test_update_payee_in_wrong_portfolio_fails(self, client: TestClient, not_my_payee_1: Payee) -> None:
        response = client.patch(
            f"/quantum/v1/payees/{not_my_payee_1.payee_id}",
            json={"name": "Coffee"},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}

    @pytest.mark.parametrize("payee_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_update_payee_with_invalid_payee_id_fails(self, client: TestClient, payee_id: int) -> None:
        response = client.patch(f"/quantum/v1/payees/{payee_id}", json={"name": "Coffee"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_payee_succeeds(self, client: TestClient, my_payee_1: Payee) -> None:
        response = client.delete(
            f"/quantum/v1/payees/{my_payee_1.payee_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_payee_in_wrong_portfolio_fails(self, client: TestClient, not_my_payee_1: Payee) -> None:
        response = client.delete(
            f"/quantum/v1/payees/{not_my_payee_1.payee_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}

    @pytest.mark.parametrize("payee_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_delete_payee_with_invalid_payee_id_fails(self, client: TestClient, payee_id: int) -> None:
        response = client.delete(f"/quantum/v1/payees/{payee_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Payee not found"}
