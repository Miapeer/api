from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import and_, desc, extract, func, or_, select
from sqlmodel.sql.expression import SelectOfScalar

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import (
    Account,
    AccountCreate,
    AccountRead,
    AccountUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.transaction import Transaction
from miapeer.models.quantum.transaction_summary import TransactionSummary

router = APIRouter(
    prefix="/accounts",
    tags=["Quantum: Accounts"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


def get_account_balance(db: DbSession, account: Account) -> int:
    # Get starting balance
    starting_balance = account.starting_balance

    # Get sum of transaction summaries
    summarized_balances_sql = (
        select(TransactionSummary)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account.account_id)
        .order_by(desc(TransactionSummary.year), desc(TransactionSummary.month))
    )

    summaries = db.exec(summarized_balances_sql).fetchall()

    sum_of_summaries = sum([ts.balance for ts in summaries])

    # Get sum of transactions that don't have summaries
    transaction_sum_sql: SelectOfScalar[Any] = (
        select(func.sum(Transaction.amount))
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account.account_id)
    )

    if len(summaries) > 0:
        latest_summary = summaries[0]
        transaction_sum_sql = transaction_sum_sql.where(
            or_(
                Transaction.clear_date == None,
                extract("year", Transaction.clear_date) > latest_summary.year,
                and_(
                    extract("year", Transaction.clear_date) == latest_summary.year,
                    extract("month", Transaction.clear_date) > latest_summary.month,
                ),
            )
        )

    transaction_sum: Optional[int] = db.exec(transaction_sum_sql).first()

    # Put them all together
    return starting_balance + sum_of_summaries + (transaction_sum if transaction_sum is not None else 0)


@router.get("/")
async def get_all_accounts(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[AccountRead]:
    sql = select(Account).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    accounts = db.exec(sql).all()

    return [
        AccountRead.model_validate(account.model_dump(), update={"balance": get_account_balance(db, account)})
        for account in accounts
    ]


@router.post("/")
async def create_account(
    db: DbSession,
    current_user: CurrentActiveUser,
    account: AccountCreate,
) -> AccountRead:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the account
    db_account = Account.model_validate(account)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    account_balance = get_account_balance(db, db_account)
    return AccountRead.model_validate(db_account.model_dump(), update={"balance": account_balance})


@router.get("/{account_id}")
async def get_account(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
) -> AccountRead:

    sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    account = db.exec(sql).one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_balance = get_account_balance(db, account)
    return AccountRead.model_validate(account.model_dump(), update={"balance": account_balance})


@router.delete("/{account_id}")
async def delete_account(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
) -> dict[str, bool]:

    sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    account = db.exec(sql).one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()

    return {"ok": True}


@router.patch("/{account_id}")
async def update_account(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    account: AccountUpdate,
) -> AccountRead:

    sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_account = db.exec(sql).one_or_none()

    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.name is not None:
        db_account.name = account.name

    if account.starting_balance is not None:
        db_account.starting_balance = account.starting_balance

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    account_balance = get_account_balance(db, db_account)
    return AccountRead.model_validate(db_account.model_dump(), update={"balance": account_balance})
