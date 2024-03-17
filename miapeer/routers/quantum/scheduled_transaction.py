from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.scheduled_transaction import (
    ScheduledTransaction,
    ScheduledTransactionCreate,
    ScheduledTransactionRead,
    ScheduledTransactionUpdate,
)

router = APIRouter(
    prefix="/accounts/{account_id}/scheduled-transactions",
    tags=["Quantum: Scheduled Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_all_scheduled_transactions(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
) -> list[ScheduledTransactionRead]:
    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(ScheduledTransaction.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    scheduled_transactions = db.exec(sql).all()
    return [
        ScheduledTransactionRead.model_validate(scheduled_transaction)
        for scheduled_transaction in scheduled_transactions
    ]


@router.post("/")
async def create_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction: ScheduledTransactionCreate,
) -> ScheduledTransactionRead:

    # Get the user's account to verify access
    sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    account = db.exec(sql).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Create the scheduled transaction
    scheduled_transaction_data = scheduled_transaction.model_dump()
    scheduled_transaction_data["account_id"] = account_id
    db_scheduled_transaction = ScheduledTransaction.model_validate(scheduled_transaction_data)
    db.add(db_scheduled_transaction)
    db.commit()
    db.refresh(db_scheduled_transaction)

    return ScheduledTransactionRead.model_validate(db_scheduled_transaction)


@router.get("/{scheduled_transaction_id}")
async def get_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
) -> ScheduledTransactionRead:

    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    scheduled_transaction = db.exec(sql).one_or_none()

    if not scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled transaction not found")

    return ScheduledTransactionRead.model_validate(scheduled_transaction)


@router.delete("/{scheduled_transaction_id}")
async def delete_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
) -> dict[str, bool]:

    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    scheduled_transaction = db.exec(sql).one_or_none()

    if not scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled transaction not found")

    db.delete(scheduled_transaction)
    db.commit()

    return {"ok": True}


@router.patch("/{scheduled_transaction_id}")
async def update_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
    scheduled_transaction: ScheduledTransactionUpdate,
) -> ScheduledTransactionRead:

    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_scheduled_transaction = db.exec(sql).one_or_none()

    if not db_scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled transaction not found")

    updated_scheduled_transaction = ScheduledTransaction.model_validate(
        db_scheduled_transaction.model_dump(), update=scheduled_transaction.model_dump()
    )

    db.add(updated_scheduled_transaction)
    db.commit()
    db.refresh(updated_scheduled_transaction)

    return ScheduledTransactionRead.model_validate(updated_scheduled_transaction)
