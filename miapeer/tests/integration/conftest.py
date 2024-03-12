from typing import Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from miapeer.app import app
from miapeer.dependencies import (
    get_current_active_user,
    get_current_user,
    get_db,
    get_jwk,
    is_miapeer_admin,
    is_miapeer_super_user,
    is_miapeer_user,
    is_quantum_admin,
    is_quantum_super_user,
    is_quantum_user,
)
from miapeer.models.miapeer import User


@pytest.fixture
def me() -> User:
    return User(user_id=91, email="its@me.com", password="", disabled=False)


@pytest.fixture
def not_me() -> User:
    return User(user_id=92, email="not@me.com", password="", disabled=False)


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


@pytest.fixture
def miapeer_user() -> bool:
    return True


@pytest.fixture
def miapeer_admin() -> bool:
    return True


@pytest.fixture
def miapeer_super_user() -> bool:
    return True


@pytest.fixture
def quantum_user() -> bool:
    return True


@pytest.fixture
def quantum_admin() -> bool:
    return True


@pytest.fixture
def quantum_super_user() -> bool:
    return True


@pytest.fixture
def returned_current_user(me: User) -> User:
    return me


@pytest.fixture(name="client")
def client_fixture(
    mock_db_session: Session,
    returned_current_user: User,
    miapeer_user: bool,
    miapeer_admin: bool,
    miapeer_super_user: bool,
    quantum_user: bool,
    quantum_admin: bool,
    quantum_super_user: bool,
) -> Iterator[TestClient]:
    def get_jwk_override() -> str:
        return "super secret key"

    def override_get_db() -> Session:
        return mock_db_session

    def override_is_miapeer_user() -> None:
        if not miapeer_user:
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_is_miapeer_admin() -> None:
        print(f"{override_is_miapeer_admin=}\n")  # TODO: Remove this!!!
        if not miapeer_admin:
            print("nope")
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_is_miapeer_super_user() -> None:
        if not miapeer_super_user:
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_is_quantum_user() -> None:
        if not quantum_user:
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_is_quantum_admin() -> None:
        if not quantum_admin:
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_is_quantum_super_user() -> None:
        if not quantum_super_user:
            raise HTTPException(status_code=400, detail="Unauthorized")

    def override_get_current_user() -> User:
        return User(user_id=returned_current_user.user_id)

    def override_get_current_active_user() -> User:
        return User(user_id=returned_current_user.user_id)

    app.dependency_overrides[get_jwk] = get_jwk_override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[is_miapeer_user] = override_is_miapeer_user
    app.dependency_overrides[is_miapeer_admin] = override_is_miapeer_admin
    app.dependency_overrides[is_miapeer_super_user] = override_is_miapeer_super_user
    app.dependency_overrides[is_quantum_user] = override_is_quantum_user
    app.dependency_overrides[is_quantum_admin] = override_is_quantum_admin
    app.dependency_overrides[is_quantum_super_user] = override_is_quantum_super_user

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
