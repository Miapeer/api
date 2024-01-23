import pytest

from miapeer.auth.jwt import JwtException, TokenData, decode_jwt


class TestDecodeJwt:
    @pytest.fixture
    def jwk(self) -> str:
        return "super secret key"

    @pytest.fixture
    def empty_token(self) -> str:
        return ""

    @pytest.fixture
    def invalid_token(self) -> str:
        return "zzz"

    @pytest.fixture
    def expired_token(self) -> str:
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6MTcwNTQ1MTk5M30.YtKDGY0yTTxYUser8mhCHrpf34NfuWH64t8FSqER7tU"

    @pytest.fixture
    def future_valid_token(self) -> str:
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.RYipfri10zKHHyAk8Vg_fRfQmKXpp_7nyjuaKRUIWmk"

    @pytest.fixture
    def future_valid_token_data(self) -> TokenData:
        return {"sub": "jep.navarra@miapeer.com", "exp": 7752937429}

    def test_no_bearer_token_raises_exception(self, empty_token: str, jwk: str) -> None:
        with pytest.raises(JwtException):
            decode_jwt(token=empty_token, jwt_key=jwk)

    def test_invalid_bearer_token_raises_exception(self, invalid_token: str, jwk: str) -> None:
        with pytest.raises(JwtException):
            decode_jwt(token=invalid_token, jwt_key=jwk)

    def test_expired_bearer_token_raises_exception(self, expired_token: str, jwk: str) -> None:
        with pytest.raises(JwtException):
            decode_jwt(token=expired_token, jwt_key=jwk)

    def test_missing_jwk_raises_exception(self, expired_token: str) -> None:
        with pytest.raises(JwtException):
            decode_jwt(token=expired_token, jwt_key="")

    def test_decodes_token(self, jwk: str, future_valid_token: str, future_valid_token_data: TokenData) -> None:
        token_data = decode_jwt(token=future_valid_token, jwt_key=jwk)
        assert token_data == future_valid_token_data


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
