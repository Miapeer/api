import pytest

from miapeer.models.miapeer import User


@pytest.fixture
def user_id() -> int:
    return 9999


@pytest.fixture
def user(user_id: int) -> User:
    return User(user_id=user_id)
