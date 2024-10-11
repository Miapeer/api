from typing import Any
from unittest.mock import Mock

import pytest

from miapeer.auth.jwt import TokenData
from miapeer.models.miapeer import User

UNSET = "fixture not set"


@pytest.fixture
def jwk() -> str:
    return "super secret key"


@pytest.fixture
def valid_jwt() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.RYipfri10zKHHyAk8Vg_fRfQmKXpp_7nyjuaKRUIWmk"


@pytest.fixture
def valid_jwt_data() -> TokenData:
    return {"sub": "jep.navarra@miapeer.com", "exp": 7752937429}


@pytest.fixture
def expired_jwt() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZWZmLm5hdmFycmFAbWlhcGVlci5jb20iLCJleHAiOjE2Nzc5ODU1NjV9.gCV8uhqs1QiMQvBVfY4RUiyVwVo7R3Sn7opRY79LeQ8"


@pytest.fixture
def jwt_missing_sub() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIiLCJleHAiOjc3NTI5Mzc0Mjl9.x37UcZkx7s_QaFpRGSCDqleB6N3rMBeknCG6iMReejM"


@pytest.fixture
def db_all_return_val():
    return UNSET


@pytest.fixture
def db_first_return_val():
    return UNSET


@pytest.fixture
def db_first_side_effect_val():
    return UNSET


@pytest.fixture
def db_one_or_none_return_val():
    return UNSET


@pytest.fixture
def db_get_return_val():
    return UNSET


@pytest.fixture
def db_refresh_patch_method():
    return UNSET


@pytest.fixture
def mock_db(
    db_all_return_val: Any,
    db_first_return_val: Any,
    db_first_side_effect_val: Any,
    db_one_or_none_return_val: Any,
    db_get_return_val: Any,
    db_refresh_patch_method: Any,
) -> Mock:
    mock_db = Mock()
    db_methods = Mock()

    db_methods.all.return_value = None if db_all_return_val == UNSET else db_all_return_val

    db_methods.first.return_value = None if db_first_return_val == UNSET else db_first_return_val
    db_methods.first.side_effect = None if db_first_side_effect_val == UNSET else db_first_side_effect_val

    db_methods.one_or_none.return_value = None if db_one_or_none_return_val == UNSET else db_one_or_none_return_val

    mock_db.get.return_value = None if db_get_return_val == UNSET else db_get_return_val

    mock_db.refresh.side_effect = None if db_refresh_patch_method == UNSET else db_refresh_patch_method

    mock_db.exec.return_value = db_methods
    return mock_db


@pytest.fixture
def user_id() -> int:
    return 9999


@pytest.fixture
def user_password() -> str:
    return "user's cool password"


@pytest.fixture
def user_hashed_password() -> str:
    return "$2b$12$5fckMX0mfWa6FR0GO/HcfOrd1wLBLl3ZRrxuZLFALBhbicjQ7AVPi"


@pytest.fixture
def user(user_id: int, user_hashed_password: str) -> User:
    return User(user_id=user_id, password=user_hashed_password, email="", disabled=False)


@pytest.fixture
def inactive_user(user_id: int, user_hashed_password: str) -> User:
    return User(user_id=user_id, password=user_hashed_password, email="", disabled=True)
