from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def db_all_return_val() -> None:
    return None


@pytest.fixture
def db_first_return_val() -> None:
    return None


@pytest.fixture
def db_one_or_none_return_val() -> None:
    return None


@pytest.fixture
def mock_db(db_all_return_val: Any, db_first_return_val: Any, db_one_or_none_return_val: Any) -> Mock:
    mock_db = Mock()

    db_methods = Mock()
    db_methods.all.return_value = db_all_return_val
    db_methods.first.return_value = db_first_return_val
    db_methods.one_or_none.return_value = db_one_or_none_return_val

    mock_db.exec.return_value = db_methods

    return mock_db
