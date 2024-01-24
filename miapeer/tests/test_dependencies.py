# # class TestGetCurrentUser:


# # # class TestGetCurrentActiveUser:
# # #     ...
# # #     # def test_inactive_user_raises_exception(self):
# # #     #     ...

# # #     # def test_returns_user(self):
# # #     #     ...


# # # import pytest
# # # from fastapi.testclient import TestClient
# # # from sqlmodel import Session, SQLModel, create_engine
# # # from sqlmodel.pool import StaticPool

# # # from .main import Hero, app, get_session


# # # @pytest.fixture(name="session")
# # # def session_fixture():
# # #     engine = create_engine(
# # #         "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
# # #     )
# # #     SQLModel.metadata.create_all(engine)
# # #     with Session(engine) as session:
# # #         yield session


# # # @pytest.fixture(name="client")
# # # def client_fixture(session: Session):
# # #     def get_session_override():
# # #         return session

# # #     app.dependency_overrides[get_session] = get_session_override
# # #     client = TestClient(app)
# # #     yield client
# # #     app.dependency_overrides.clear()


# # # def test_create_hero(client: TestClient):
# # #     response = client.post(
# # #         "/heroes/", json={"name": "Deadpond", "secret_name": "Dive Wilson"}
# # #     )
# # #     data = response.json()

# # #     assert response.status_code == 200
# # #     assert data["name"] == "Deadpond"
# # #     assert data["secret_name"] == "Dive Wilson"
# # #     assert data["age"] is None
# # #     assert data["id"] is not None
