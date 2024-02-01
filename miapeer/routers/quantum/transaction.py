from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)

router = APIRouter(
    prefix="/accounts/{account_id}/transactions",
    tags=["Quantum: Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)])
async def get_all_transactions(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
) -> list[TransactionRead]:
    sql = (
        select(Transaction)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Transaction.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transactions = db.exec(sql).all()
    return [TransactionRead.model_validate(transaction) for transaction in transactions]


@router.post("/", dependencies=[Depends(is_quantum_user)])
async def create_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction: TransactionCreate,
) -> TransactionRead:

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

    # Create the transaction
    transaction_data = transaction.model_dump()
    transaction_data["account_id"] = account_id
    db_transaction = Transaction.model_validate(transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return TransactionRead.model_validate(db_transaction)


@router.get("/{transaction_id}", dependencies=[Depends(is_quantum_user)])
async def get_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction_id: int,
) -> TransactionRead:

    sql = (
        select(Transaction)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(Transaction.transaction_id == transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transaction = db.exec(sql).one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionRead.model_validate(transaction)


@router.delete("/{transaction_id}", dependencies=[Depends(is_quantum_user)])
async def delete_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction_id: int,
) -> dict[str, bool]:

    sql = (
        select(Transaction)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(Transaction.transaction_id == transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transaction = db.exec(sql).one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()

    return {"ok": True}


@router.patch("/{transaction_id}", dependencies=[Depends(is_quantum_user)])
async def update_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction_id: int,
    transaction: TransactionUpdate,
) -> TransactionRead:

    sql = (
        select(Transaction)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(Transaction.transaction_id == transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_transaction = db.exec(sql).one_or_none()

    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updated_transaction = Transaction.model_validate(db_transaction.model_dump(), update=transaction.model_dump())

    db.add(updated_transaction)
    db.commit()
    db.refresh(updated_transaction)

    return TransactionRead.model_validate(updated_transaction)
