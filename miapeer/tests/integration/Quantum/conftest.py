from datetime import date

import pytest
from sqlmodel import Session

from miapeer.models.miapeer import User
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.scheduled_transaction import ScheduledTransaction
from miapeer.models.quantum.transaction import Transaction
from miapeer.models.quantum.transaction_type import TransactionType


@pytest.fixture
def my_portfolio() -> Portfolio:
    return Portfolio(portfolio_id=1)


@pytest.fixture
def not_my_portfolio() -> Portfolio:
    return Portfolio(portfolio_id=2)


@pytest.fixture
def my_account_1(my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        account_id=11,
        name="my acct 1",
        starting_balance=101,
    )


@pytest.fixture
def my_account_2(my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        account_id=12,
        name="my acct 2",
        starting_balance=102,
    )


@pytest.fixture
def not_my_account_1(not_my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        account_id=21,
        name="not my acct 1",
        starting_balance=201,
    )


@pytest.fixture
def not_my_account_2(not_my_portfolio: Portfolio) -> Account:
    return Account(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        account_id=22,
        name="not my acct 2",
        starting_balance=202,
    )


@pytest.fixture
def my_payee_1(my_portfolio: Portfolio) -> Payee:
    return Payee(portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0, payee_id=31, name="my payee 1")


@pytest.fixture
def my_payee_2(my_portfolio: Portfolio) -> Payee:
    return Payee(portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0, payee_id=32, name="my payee 2")


@pytest.fixture
def not_my_payee_1(not_my_portfolio: Portfolio) -> Payee:
    return Payee(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        payee_id=41,
        name="not my payee 1",
    )


@pytest.fixture
def not_my_payee_2(not_my_portfolio: Portfolio) -> Payee:
    return Payee(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        payee_id=42,
        name="not my payee 2",
    )


@pytest.fixture
def my_category_1(my_portfolio: Portfolio) -> Category:
    return Category(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        category_id=51,
        name="my category 1",
    )


@pytest.fixture
def my_category_2(my_portfolio: Portfolio) -> Category:
    return Category(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        category_id=52,
        name="my category 2",
    )


@pytest.fixture
def not_my_category_1(not_my_portfolio: Portfolio) -> Category:
    return Category(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        category_id=61,
        name="not my category 1",
    )


@pytest.fixture
def not_my_category_2(not_my_portfolio: Portfolio) -> Category:
    return Category(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        category_id=62,
        name="not my category 2",
    )


@pytest.fixture
def my_transaction_type_1(my_portfolio: Portfolio) -> TransactionType:
    return TransactionType(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        transaction_type_id=71,
        name="my transaction type 1",
    )


@pytest.fixture
def my_transaction_type_2(my_portfolio: Portfolio) -> TransactionType:
    return TransactionType(
        portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
        transaction_type_id=72,
        name="my transaction type 2",
    )


@pytest.fixture
def not_my_transaction_type_1(not_my_portfolio: Portfolio) -> TransactionType:
    return TransactionType(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        transaction_type_id=81,
        name="not my transaction type 1",
    )


@pytest.fixture
def not_my_transaction_type_2(not_my_portfolio: Portfolio) -> TransactionType:
    return TransactionType(
        portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
        transaction_type_id=82,
        name="not my transaction type 2",
    )


@pytest.fixture
def my_minimal_transaction(my_account_1: Account) -> Transaction:
    return Transaction(
        account_id=my_account_1.account_id,
        transaction_id=100,
        transaction_type_id=None,
        payee_id=None,
        category_id=None,
        amount=-0,
        transaction_date=date.today(),
        clear_date=None,
        check_number=None,
        exclude_from_forecast=True,
        notes=None,
    )


@pytest.fixture
def my_debit_transaction(my_account_1: Account, my_transaction_type_1: TransactionType, my_payee_2: Payee, my_category_1: Category) -> Transaction:
    return Transaction(
        account_id=my_account_1.account_id,
        transaction_id=101,
        transaction_type_id=my_transaction_type_1.transaction_type_id,
        payee_id=my_payee_2.payee_id,
        category_id=my_category_1.category_id,
        amount=-13,
        transaction_date=date.today(),
        clear_date=date.today(),
        check_number="123",
        exclude_from_forecast=True,
        notes="transaction note 1",
    )


@pytest.fixture
def my_credit_transaction(my_account_1: Account, my_transaction_type_2: TransactionType, my_payee_1: Payee, my_category_2: Category) -> Transaction:
    return Transaction(
        account_id=my_account_1.account_id if my_account_1.account_id else 0,
        transaction_id=102,
        transaction_type_id=my_transaction_type_2.transaction_type_id,
        payee_id=my_payee_1.payee_id,
        category_id=my_category_2.category_id,
        amount=864,
        transaction_date=date.today(),
        clear_date=None,
        check_number=None,
        exclude_from_forecast=False,
        notes="transaction note 2",
    )


@pytest.fixture
def not_my_debit_transaction(
    not_my_account_1: Account,
    not_my_transaction_type_1: TransactionType,
    not_my_payee_2: Payee,
    not_my_category_1: Category,
) -> Transaction:
    return Transaction(
        account_id=not_my_account_1.account_id if not_my_account_1.account_id else 0,
        transaction_id=111,
        transaction_type_id=not_my_transaction_type_1.transaction_type_id,
        payee_id=not_my_payee_2.payee_id,
        category_id=not_my_category_1.category_id,
        amount=-999,
        transaction_date=date.today(),
        clear_date=date.today(),
        check_number=None,
        exclude_from_forecast=True,
        notes="not my transaction note 1",
    )


@pytest.fixture
def not_my_credit_transaction(
    not_my_account_1: Account,
    not_my_transaction_type_2: TransactionType,
    not_my_payee_1: Payee,
    not_my_category_2: Category,
) -> Transaction:
    return Transaction(
        account_id=not_my_account_1.account_id if not_my_account_1.account_id else 0,
        transaction_id=112,
        transaction_type_id=not_my_transaction_type_2.transaction_type_id,
        payee_id=not_my_payee_1.payee_id,
        category_id=not_my_category_2.category_id,
        amount=98347,
        transaction_date=date.today(),
        clear_date=None,
        check_number="456",
        exclude_from_forecast=False,
        notes="not my transaction note 2",
    )


@pytest.fixture
def my_minimal_scheduled_transaction(my_account_1: Account) -> ScheduledTransaction:
    return ScheduledTransaction(
        account_id=my_account_1.account_id if my_account_1.account_id else 0,
        scheduled_transaction_id=981,
        transaction_type_id=None,
        payee_id=None,
        category_id=None,
        fixed_amount=2349,
        estimate_occurrences=None,
        prompt_days=None,
        start_date=date.today(),
        end_date=None,
        limit_occurrences=None,
        repeat_option_id=None,
        notes=None,
        on_autopay=False,
    )


@pytest.fixture
def my_scheduled_transaction(
    my_account_1: Account, my_transaction_type_1: TransactionType, my_payee_2: Payee, my_category_1: Category
) -> ScheduledTransaction:
    return ScheduledTransaction(
        account_id=my_account_1.account_id if my_account_1.account_id else 0,
        scheduled_transaction_id=982,
        transaction_type_id=my_transaction_type_1.transaction_type_id,
        payee_id=my_payee_2.payee_id,
        category_id=my_category_1.category_id,
        fixed_amount=2349,
        estimate_occurrences=3,
        prompt_days=7,
        start_date=date.today(),
        end_date=date.today(),
        limit_occurrences=10,
        repeat_option_id=2,
        notes="My scheduled transaction detail",
        on_autopay=True,
    )


@pytest.fixture
def not_my_scheduled_transaction(
    not_my_account_1: Account,
    not_my_transaction_type_2: TransactionType,
    not_my_payee_1: Payee,
    not_my_category_2: Category,
) -> ScheduledTransaction:
    return ScheduledTransaction(
        account_id=not_my_account_1.account_id if not_my_account_1.account_id else 0,
        scheduled_transaction_id=983,
        transaction_type_id=not_my_transaction_type_2.transaction_type_id,
        payee_id=not_my_payee_1.payee_id,
        category_id=not_my_category_2.category_id,
        fixed_amount=-4982,
        estimate_occurrences=None,
        prompt_days=None,
        start_date=date.today(),
        end_date=None,
        limit_occurrences=None,
        repeat_option_id=None,
        notes=None,
        on_autopay=False,
    )


# @pytest.fixture
# def insert_transaction_summary(mock_db_session: Session, account_id: int) -> None:
#     TransactionSummary(account_id=account_id, year=1, month=1, balance=987),


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
    my_payee_1: Payee,
    my_payee_2: Payee,
    not_my_payee_1: Payee,
    not_my_payee_2: Payee,
    my_category_1: Category,
    my_category_2: Category,
    not_my_category_1: Category,
    not_my_category_2: Category,
    my_transaction_type_1: TransactionType,
    my_transaction_type_2: TransactionType,
    not_my_transaction_type_1: TransactionType,
    not_my_transaction_type_2: TransactionType,
    my_minimal_transaction: Transaction,
    my_debit_transaction: Transaction,
    my_credit_transaction: Transaction,
    not_my_debit_transaction: Transaction,
    not_my_credit_transaction: Transaction,
    my_minimal_scheduled_transaction: ScheduledTransaction,
    my_scheduled_transaction: ScheduledTransaction,
    not_my_scheduled_transaction: ScheduledTransaction,
) -> None:
    mock_db_session.add_all([me, not_me])

    mock_db_session.add_all([my_portfolio, not_my_portfolio])

    mock_db_session.add_all(
        [
            PortfolioUser(
                portfolio_id=my_portfolio.portfolio_id if my_portfolio.portfolio_id else 0,
                user_id=me.user_id if me.user_id else 0,
            ),
            PortfolioUser(
                portfolio_id=not_my_portfolio.portfolio_id if not_my_portfolio.portfolio_id else 0,
                user_id=not_me.user_id if not_me.user_id else 0,
            ),
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

    mock_db_session.add_all([my_payee_1, my_payee_2, not_my_payee_1, not_my_payee_2])

    mock_db_session.add_all([my_category_1, my_category_2, not_my_category_1, not_my_category_2])

    mock_db_session.add_all([my_transaction_type_1, my_transaction_type_2, not_my_transaction_type_1, not_my_transaction_type_2])

    mock_db_session.add_all(
        [
            my_minimal_transaction,
            my_debit_transaction,
            my_credit_transaction,
            not_my_debit_transaction,
            not_my_credit_transaction,
        ]
    )

    mock_db_session.add_all(
        [
            my_minimal_scheduled_transaction,
            my_scheduled_transaction,
            not_my_scheduled_transaction,
        ]
    )

    mock_db_session.commit()
