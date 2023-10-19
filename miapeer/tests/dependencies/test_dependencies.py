# import pytest

# from miapeer.dependencies import _decode_jwt, get_current_user, CredentialErrorMessage
# # from miapeer.dependencies import get_current_active_user
# from fastapi import HTTPException

# pytestmark = pytest.mark.asyncio


# class TestDecodeJwt:
#     @pytest.fixture
#     def jwk(self):
#         return "super secret key"

#     @pytest.fixture
#     def empty_token(self):
#         return ""

#     @pytest.fixture
#     def invalid_token(self):
#         return "zzz"

#     @pytest.fixture
#     def expired_token(self):
#         return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXBuMTNAZ21haWwuY29tIiwiZXhwIjoxNjc3OTg1NTY1fQ.pXj4Rk42O5iJB1XhIRWfVCO-fSdnuCXEJwLW5G1NU64"

#     async def test_no_bearer_token_raises_exception(self, empty_token, jwk):
#         with pytest.raises(HTTPException):
#             await _decode_jwt(token=empty_token, jwt_key=jwk)

#     async def test_invalid_bearer_token_raises_exception(self, invalid_token, jwk):
#         with pytest.raises(HTTPException):
#             await _decode_jwt(token=invalid_token, jwt_key=jwk)

#     async def test_expired_bearer_token_raises_exception(self, expired_token, jwk):
#         with pytest.raises(HTTPException):
#             await _decode_jwt(token=expired_token, jwt_key=jwk)

#     async def test_missing_jwk_raises_exception(self):
#         ...

#     async def test_decode_fail_raises_exception(self):
#         ...

#     async def test_decodes_token(self):
#         ...


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
