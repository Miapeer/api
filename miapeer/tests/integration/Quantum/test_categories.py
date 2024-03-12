import pytest
from fastapi.testclient import TestClient

from miapeer.models.quantum.category import Category
from miapeer.models.quantum.portfolio import Portfolio


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetAll:
    def test_get_all_categories_in_portfolio(
        self, client: TestClient, my_category_1: Category, my_category_2: Category
    ) -> None:
        response = client.get(
            "/quantum/v1/categories",
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "portfolio_id": my_category_1.portfolio_id,
                "category_id": my_category_1.category_id,
                "parent_category_id": None,
                "name": my_category_1.name,
            },
            {
                "portfolio_id": my_category_2.portfolio_id,
                "category_id": my_category_2.category_id,
                "parent_category_id": None,
                "name": my_category_2.name,
            },
        ]


@pytest.mark.usefixtures("create_complete_portfolio")
class TestCreate:
    def test_create_category(self, client: TestClient, my_portfolio: Portfolio, not_my_category_2: Category) -> None:
        response = client.post(
            "/quantum/v1/categories",
            json={"portfolio_id": my_portfolio.portfolio_id, "name": "Coffee"},
        )

        category_id = 0
        if not_my_category_2.category_id is not None:
            category_id = not_my_category_2.category_id

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_portfolio.portfolio_id,
            "category_id": (category_id + 1),  # Increment by 1, the last account ID inserted
            "parent_category_id": None,
            "name": "Coffee",
        }


@pytest.mark.usefixtures("create_complete_portfolio")
class TestGetOne:
    def test_get_one_category_in_portfolio_succeeds(self, client: TestClient, my_category_1: Category) -> None:
        response = client.get(f"/quantum/v1/categories/{my_category_1.category_id}")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_category_1.portfolio_id,
            "category_id": my_category_1.category_id,
            "parent_category_id": None,
            "name": my_category_1.name,
        }

    def test_get_one_category_in_wrong_portfolio_fails(self, client: TestClient, not_my_category_1: Category) -> None:
        response = client.get(f"/quantum/v1/categories/{not_my_category_1.category_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}

    @pytest.mark.parametrize("category_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_get_one_category_with_invalid_category_id_fails(self, client: TestClient, category_id: int) -> None:
        response = client.get(f"/quantum/v1/categories/{category_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestUpdate:
    def test_update_category_succeeds(self, client: TestClient, my_category_1: Category) -> None:
        response = client.patch(
            f"/quantum/v1/categories/{my_category_1.category_id}",
            json={"name": "Coffee"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": my_category_1.portfolio_id,
            "category_id": my_category_1.category_id,
            "parent_category_id": None,
            "name": "Coffee",
        }

    def test_update_category_in_wrong_portfolio_fails(self, client: TestClient, not_my_category_1: Category) -> None:
        response = client.patch(
            f"/quantum/v1/categories/{not_my_category_1.category_id}",
            json={"name": "Coffee"},
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}

    @pytest.mark.parametrize("category_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_update_category_with_invalid_category_id_fails(self, client: TestClient, category_id: int) -> None:
        response = client.patch(f"/quantum/v1/categories/{category_id}", json={"name": "Coffee"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}


@pytest.mark.usefixtures("create_complete_portfolio")
class TestDelete:
    def test_delete_category_succeeds(self, client: TestClient, my_category_1: Category) -> None:
        response = client.delete(
            f"/quantum/v1/categories/{my_category_1.category_id}",
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_category_in_wrong_portfolio_fails(self, client: TestClient, not_my_category_1: Category) -> None:
        response = client.delete(
            f"/quantum/v1/categories/{not_my_category_1.category_id}",
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}

    @pytest.mark.parametrize("category_id", [0, -1, 999999999999999999, -999999999999999999])
    def test_delete_category_with_invalid_category_id_fails(self, client: TestClient, category_id: int) -> None:
        response = client.delete(f"/quantum/v1/categories/{category_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Category not found"}
