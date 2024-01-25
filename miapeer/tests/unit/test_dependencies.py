from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer import dependencies
from miapeer.models.miapeer import User

pytestmark = pytest.mark.asyncio


class TestGetCurrentUser:
    @pytest.mark.parametrize("db_first_return_val", ["some data", 123])
    async def test_get_current_user(self, mock_db: Mock, valid_jwt: str, jwk: str, db_first_return_val: Any) -> None:
        res = await dependencies.get_current_user(token=valid_jwt, jwt_key=jwk, db=mock_db)
        assert res == db_first_return_val

    async def test_get_current_user_raises_exception_when_username_not_provided(
        self, mock_db: Mock, jwt_missing_sub: str, jwk: str
    ) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_user(token=jwt_missing_sub, jwt_key=jwk, db=mock_db)

    @pytest.mark.parametrize("db_first_return_val", [None])
    async def test_get_current_user_raises_exception_when_user_not_found(
        self, mock_db: Mock, valid_jwt: str, jwk: str
    ) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_user(token=valid_jwt, jwt_key=jwk, db=mock_db)


class TestGetCurrentActiveUser:
    async def test_returns_user(self, user: User) -> None:
        returned_user = await dependencies.get_current_active_user(current_user=user)
        assert returned_user == user

    async def test_inactive_user_raises_exception(self, inactive_user: User) -> None:
        with pytest.raises(HTTPException):
            await dependencies.get_current_active_user(current_user=inactive_user)


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
