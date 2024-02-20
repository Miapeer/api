import pytest
from fastapi.testclient import TestClient


class TestCreate:
    @pytest.mark.usefixtures(
        "insert_portfolio", "insert_portfolio_user", "insert_debit_transaction", "insert_transaction_summary"
    )
    def test_get_accounts(self, client: TestClient, valid_jwt: str) -> None:
        response = client.post(
            "/quantum/v1/accounts",
            headers={"Authorization": "bearer " + valid_jwt},
            json={"portfolio_id": 1, "name": "apple pies", "starting_balance": 12345},
        )
        assert response.status_code == 200
        assert response.json() == {
            "name": "apple pies",
            "portfolio_id": 1,
            "account_id": 1,
            "starting_balance": 12345,
            "balance": 12345 + 987 - 13,
        }


# def test_create_user():
#     response = client.post(
#         "/users/",
#         json={"email": "deadpool@example.com", "password": "chimichangas4life"},
#     )
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["email"] == "deadpool@example.com"
#     assert "id" in data
#     user_id = data["id"]

#     response = client.get(f"/users/{user_id}")
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["email"] == "deadpool@example.com"
#     assert data["id"] == user_id


# def test_read_item_bad_token():
#     response = client.get("/items/foo", headers={"X-Token": "hailhydra"})
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Invalid X-Token header"}


# def test_read_inexistent_item():
#     response = client.get("/items/baz", headers={"X-Token": "coneofsilence"})
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Item not found"}


# def test_create_item():
#     response = client.post(
#         "/items/",
#         headers={"X-Token": "coneofsilence"},
#         json={"id": "foobar", "title": "Foo Bar", "description": "The Foo Barters"},
#     )
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": "foobar",
#         "title": "Foo Bar",
#         "description": "The Foo Barters",
#     }


# def test_create_item_bad_token():
#     response = client.post(
#         "/items/",
#         headers={"X-Token": "hailhydra"},
#         json={"id": "bazz", "title": "Bazz", "description": "Drop the bazz"},
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Invalid X-Token header"}


# def test_create_existing_item():
#     response = client.post(
#         "/items/",
#         headers={"X-Token": "coneofsilence"},
#         json={
#             "id": "foo",
#             "title": "The Foo ID Stealers",
#             "description": "There goes my stealer",
#         },
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Item already exists"}

# def test_create_hero():
#         # Some code here omitted, we will see it later 👈
#         client = TestClient(app)  #

#         response = client.post(  #
#             "/heroes/", json={"name": "Deadpond", "secret_name": "Dive Wilson"}
#         )
#         # Some code here omitted, we will see it later 👈
#         data = response.json()  #

#         assert response.status_code == 200  #
#         assert data["name"] == "Deadpond"  #
#         assert data["secret_name"] == "Dive Wilson"  #
#         assert data["age"] is None  #
#         assert data["id"] is not None  #


#################################


# import pytest
# from fastapi.testclient import TestClient
# from sqlmodel import Session, SQLModel, create_engine
# from sqlmodel.pool import StaticPool

# from .main import Hero, app, get_session


# @pytest.fixture(name="session")
# def session_fixture():
#     engine = create_engine(
#         "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
#     )
#     SQLModel.metadata.create_all(engine)
#     with Session(engine) as session:
#         yield session


# @pytest.fixture(name="client")
# def client_fixture(session: Session):
#     def get_session_override():
#         return session

#     app.dependency_overrides[get_session] = get_session_override
#     client = TestClient(app)
#     yield client
#     app.dependency_overrides.clear()


# def test_create_hero(client: TestClient):
#     response = client.post(
#         "/heroes/", json={"name": "Deadpond", "secret_name": "Dive Wilson"}
#     )
#     data = response.json()

#     assert response.status_code == 200
#     assert data["name"] == "Deadpond"
#     assert data["secret_name"] == "Dive Wilson"
#     assert data["age"] is None
#     assert data["id"] is not None


# def test_create_hero_incomplete(client: TestClient):
#     # No secret_name
#     response = client.post("/heroes/", json={"name": "Deadpond"})
#     assert response.status_code == 422


# def test_create_hero_invalid(client: TestClient):
#     # secret_name has an invalid type
#     response = client.post(
#         "/heroes/",
#         json={
#             "name": "Deadpond",
#             "secret_name": {"message": "Do you wanna know my secret identity?"},
#         },
#     )
#     assert response.status_code == 422


# def test_read_heroes(session: Session, client: TestClient):
#     hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
#     hero_2 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
#     session.add(hero_1)
#     session.add(hero_2)
#     session.commit()

#     response = client.get("/heroes/")
#     data = response.json()

#     assert response.status_code == 200

#     assert len(data) == 2
#     assert data[0]["name"] == hero_1.name
#     assert data[0]["secret_name"] == hero_1.secret_name
#     assert data[0]["age"] == hero_1.age
#     assert data[0]["id"] == hero_1.id
#     assert data[1]["name"] == hero_2.name
#     assert data[1]["secret_name"] == hero_2.secret_name
#     assert data[1]["age"] == hero_2.age
#     assert data[1]["id"] == hero_2.id


# def test_read_hero(session: Session, client: TestClient):
#     hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
#     session.add(hero_1)
#     session.commit()

#     response = client.get(f"/heroes/{hero_1.id}")
#     data = response.json()

#     assert response.status_code == 200
#     assert data["name"] == hero_1.name
#     assert data["secret_name"] == hero_1.secret_name
#     assert data["age"] == hero_1.age
#     assert data["id"] == hero_1.id


# def test_update_hero(session: Session, client: TestClient):
#     hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
#     session.add(hero_1)
#     session.commit()

#     response = client.patch(f"/heroes/{hero_1.id}", json={"name": "Deadpuddle"})
#     data = response.json()

#     assert response.status_code == 200
#     assert data["name"] == "Deadpuddle"
#     assert data["secret_name"] == "Dive Wilson"
#     assert data["age"] is None
#     assert data["id"] == hero_1.id


# def test_delete_hero(session: Session, client: TestClient):
#     hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
#     session.add(hero_1)
#     session.commit()

#     response = client.delete(f"/heroes/{hero_1.id}")

#     hero_in_db = session.get(Hero, hero_1.id)

#     assert response.status_code == 200

#     assert hero_in_db is None
