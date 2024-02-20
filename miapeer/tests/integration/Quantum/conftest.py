import pytest
from sqlmodel import Session

from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.transaction import Transaction
from miapeer.models.quantum.transaction_summary import TransactionSummary


@pytest.fixture
def insert_portfolio(mock_db_session: Session) -> None:
    mock_db_session.add_all(
        [
            Portfolio(portfolio_id=1),
        ]
    )
    mock_db_session.commit()


@pytest.fixture
def insert_portfolio_user(mock_db_session: Session) -> None:
    mock_db_session.add_all(
        [
            PortfolioUser(portfolio_id=1, user_id=1),
        ]
    )
    mock_db_session.commit()


@pytest.fixture
def insert_debit_transaction(mock_db_session: Session) -> None:
    mock_db_session.add_all(
        [
            Transaction(account_id=1, amount=-13),
        ]
    )
    mock_db_session.commit()


@pytest.fixture
def insert_transaction_summary(mock_db_session: Session) -> None:
    mock_db_session.add_all(
        [
            TransactionSummary(account_id=1, year=1, month=1, balance=987),
        ]
    )
    mock_db_session.commit()


# @pytest.fixture
# def insert_application(mock_db_session):
#     mock_db_session.exec(text("insert into miapeer_application (name, url, description, icon, display) values ('Quantum', 'url', 'desc', 'icon', 1)"))

# @pytest.fixture
# def insert_role(mock_db_session):
#     mock_db_session.exec(text("insert into miapeer_role (name) values ('User')"))

# @pytest.fixture
# def insert_application_role(mock_db_session):
#     mock_db_session.exec(text("insert into miapeer_application_role (application_id, role_id, description) values (1, 1, 'desc')"))

# @pytest.fixture
# def insert_user(mock_db_session):
#     mock_db_session.exec(text("insert into miapeer_user (email, password, disabled) values ('jep.navarra@miapeer.com', '', false)"))

# @pytest.fixture
# def insert_permission(mock_db_session):
#     mock_db_session.exec(text("insert into miapeer_permission (user_id, application_role_id) values (1, 1)"))
