import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.portfolio import Portfolio


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_user_portfolios(self, client: TestClient, my_portfolio: Portfolio) -> None:
        response = client.get(
            "/quantum/v1/portfolios",
        )

        assert response.status_code == 200
        assert response.json() == [{"portfolio_id": 1}]


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    def test_create_portfolio(self, client: TestClient, not_my_portfolio: Portfolio) -> None:
        response = client.post(
            "/quantum/v1/portfolios",
            json={},
        )

        portfolio_id = 0
        if not_my_portfolio.portfolio_id is not None:
            portfolio_id = not_my_portfolio.portfolio_id

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": portfolio_id + 1,  # Increment by 1, the last portfolio ID inserted
        }


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_portfolio_succeeds(self, client: TestClient, my_portfolio: Portfolio) -> None:
        response = client.get(f"/quantum/v1/portfolios/{my_portfolio.portfolio_id}")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_portfolio.portfolio_id,
        }

    def test_get_one_portfolio_that_is_not_mine_fails(self, client: TestClient, not_my_portfolio: Portfolio) -> None:
        response = client.get(f"/quantum/v1/portfolios/{not_my_portfolio.portfolio_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Portfolio not found"}

    @pytest.mark.parametrize("portfolio_id", [0, -1, -999999999999999999])
    def test_get_one_account_with_invalid_portfolio_id_fails(self, client: TestClient, portfolio_id: int) -> None:
        response = client.get(f"/quantum/v1/portfolios/{portfolio_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Portfolio not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    # This is the only test case since only a Quantum Super User can delete a portfolio. The owner cannot perform this action.
    def test_delete_account_succeeds(self, client: TestClient, my_portfolio: Portfolio) -> None:
        response = client.delete(
            f"/quantum/v1/portfolios/{my_portfolio.portfolio_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}


# NB: There is no functionality for updating a portfolio
