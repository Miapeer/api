import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.account import Account
from miapeer.models.quantum.portfolio import Portfolio


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_accounts_in_portfolio(
        self, client: TestClient, my_account_1: Account, my_account_2: Account
    ) -> None:
        response = client.get(
            "/quantum/v1/accounts",
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "portfolio_id": my_account_1.portfolio_id,
                "account_id": my_account_1.account_id,
                "name": my_account_1.name,
                "starting_balance": my_account_1.starting_balance,
                "balance": my_account_1.starting_balance,
            },
            {
                "portfolio_id": my_account_2.portfolio_id,
                "account_id": my_account_2.account_id,
                "name": my_account_2.name,
                "starting_balance": my_account_2.starting_balance,
                "balance": my_account_2.starting_balance,
            },
        ]


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    def test_create_account(self, client: TestClient, my_portfolio: Portfolio, not_my_account_2: Account) -> None:
        response = client.post(
            "/quantum/v1/accounts",
            json={"portfolio_id": my_portfolio.portfolio_id, "name": "apple pies", "starting_balance": 12345},
        )

        account_id = 0
        if not_my_account_2.account_id is not None:
            account_id = not_my_account_2.account_id

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_portfolio.portfolio_id,
            "name": "apple pies",
            "starting_balance": 12345,
            "account_id": (account_id + 1),  # Increment by 1, the last account ID inserted
            "balance": 12345,
        }


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_account_in_portfolio_succeeds(self, client: TestClient, my_account_1: Account) -> None:
        response = client.get(f"/quantum/v1/accounts/{my_account_1.account_id}")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_account_1.portfolio_id,
            "account_id": my_account_1.account_id,
            "name": my_account_1.name,
            "starting_balance": my_account_1.starting_balance,
            "balance": my_account_1.starting_balance,
        }

    def test_get_one_account_in_wrong_portfolio_fails(self, client: TestClient, not_my_account_1: Account) -> None:
        response = client.get(f"/quantum/v1/accounts/{not_my_account_1.account_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}

    @pytest.mark.parametrize("account_id", [0, -1, -999999999999999999])
    def test_get_one_account_with_invalid_account_id_fails(self, client: TestClient, account_id: int) -> None:
        response = client.get(f"/quantum/v1/accounts/{account_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    def test_update_account_succeeds(self, client: TestClient, my_account_1: Account) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{my_account_1.account_id}",
            json={"name": "peach cobbler", "starting_balance": 543},
        )

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_account_1.portfolio_id,
            "account_id": my_account_1.account_id,
            "name": "peach cobbler",
            "starting_balance": 543,
            "balance": 543,
        }

    def test_update_account_in_wrong_portfolio_fails(self, client: TestClient, not_my_account_1: Account) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{not_my_account_1.account_id}",
            json={"name": "peach cobbler", "starting_balance": 543},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}

    @pytest.mark.parametrize("account_id", [0, -1, -999999999999999999])
    def test_update_account_with_invalid_account_id_fails(self, client: TestClient, account_id: int) -> None:
        response = client.patch(
            f"/quantum/v1/accounts/{account_id}", json={"name": "peach cobbler", "starting_balance": 543}
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_account_succeeds(self, client: TestClient, my_account_1: Account) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{my_account_1.account_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_account_in_wrong_portfolio_fails(self, client: TestClient, not_my_account_1: Account) -> None:
        response = client.delete(
            f"/quantum/v1/accounts/{not_my_account_1.account_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}

    @pytest.mark.parametrize("account_id", [0, -1, -999999999999999999])
    def test_delete_account_with_invalid_account_id_fails(self, client: TestClient, account_id: int) -> None:
        response = client.delete(f"/quantum/v1/accounts/{account_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}
