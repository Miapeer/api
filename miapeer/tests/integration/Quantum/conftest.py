import pytest
from sqlmodel import Session

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser


@pytest.fixture
def my_portfolio() -> Portfolio:
    return Portfolio(portfolio_id=1)


@pytest.fixture
def not_my_portfolio() -> Portfolio:
    return Portfolio(portfolio_id=2)


@pytest.fixture
def my_account_1(my_portfolio: Portfolio) -> Account:
    return Account(portfolio_id=my_portfolio.portfolio_id, account_id=11, name="my acct 1", starting_balance=101)


@pytest.fixture
def my_account_2(my_portfolio: Portfolio) -> Account:
    return Account(portfolio_id=my_portfolio.portfolio_id, account_id=12, name="my acct 2", starting_balance=102)


@pytest.fixture
def not_my_account_1(not_my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=not_my_portfolio.portfolio_id, account_id=21, name="not my acct 1", starting_balance=201
    )


@pytest.fixture
def not_my_account_2(not_my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=not_my_portfolio.portfolio_id, account_id=22, name="not my acct 2", starting_balance=202
    )


# @pytest.fixture
# def insert_debit_transaction(mock_db_session: Session, account_id: int) -> None:
#     mock_db_session.add_all(
#         [
#             Transaction(account_id=account_id, amount=-13),
#         ]
#     )
#     mock_db_session.commit()


# @pytest.fixture
# def insert_transaction_summary(mock_db_session: Session, account_id: int) -> None:
#     mock_db_session.add_all(
#         [
#             TransactionSummary(account_id=account_id, year=1, month=1, balance=987),
#         ]
#     )
#     mock_db_session.commit()


@pytest.fixture
def create_complete_portfolio(
    mock_db_session: Session,
    my_portfolio: Portfolio,
    not_my_portfolio: Portfolio,
    me: User,
    not_me: User,
    my_account_1: Account,
    my_account_2: Account,
    not_my_account_1: Account,
    not_my_account_2: Account,
) -> None:
    mock_db_session.add_all([me, not_me])

    mock_db_session.add_all([my_portfolio, not_my_portfolio])

    mock_db_session.add_all(
        [
            PortfolioUser(portfolio_id=my_portfolio.portfolio_id, user_id=me.user_id),
            PortfolioUser(portfolio_id=not_my_portfolio.portfolio_id, user_id=not_me.user_id),
        ]
    )

    mock_db_session.add_all(
        [
            my_account_1,
            my_account_2,
            not_my_account_1,
            not_my_account_2,
        ]
    )

    mock_db_session.commit()
