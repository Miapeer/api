from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from miapeer.app import app
from miapeer.dependencies import (
    get_current_active_user,
    get_db,
    get_jwk,
    is_quantum_user,
)
from miapeer.models.miapeer import User


@pytest.fixture
def valid_jwt() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.RYipfri10zKHHyAk8Vg_fRfQmKXpp_7nyjuaKRUIWmk"


@pytest.fixture
def mock_db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        echo=False,
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(mock_db_session: Session) -> Iterator[TestClient]:
    def get_jwk_override() -> str:
        return "super secret key"

    def override_get_db() -> Session:
        return mock_db_session

    def override_is_quantum_user() -> bool:
        return True

    def override_get_current_active_user() -> User:
        return User(user_id=1)

    app.dependency_overrides[get_jwk] = get_jwk_override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[is_quantum_user] = override_is_quantum_user

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
