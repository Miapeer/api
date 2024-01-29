from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_current_active_user,
    get_db,
    is_quantum_user,
)
from miapeer.models.miapeer import User
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
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[ScheduledTransactionRead])
async def get_all_scheduled_transactions(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ScheduledTransaction]:

    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(ScheduledTransaction.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    scheduled_transactions = list(db.exec(sql).all())

    return scheduled_transactions


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=ScheduledTransactionRead)
async def create_scheduled_transaction(
    account_id: int,
    scheduled_transaction: ScheduledTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScheduledTransaction:

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
    db_scheduled_transaction = ScheduledTransaction(**scheduled_transaction_data)
    db.add(db_scheduled_transaction)
    db.commit()
    db.refresh(db_scheduled_transaction)

    return db_scheduled_transaction


@router.get(
    "/{scheduled_transaction_id}", dependencies=[Depends(is_quantum_user)], response_model=ScheduledTransaction
)
async def get_scheduled_transaction(
    account_id: int,
    scheduled_transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScheduledTransaction:

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

    return scheduled_transaction


@router.delete("/{scheduled_transaction_id}", dependencies=[Depends(is_quantum_user)])
async def delete_scheduled_transaction(
    account_id: int,
    scheduled_transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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


@router.patch(
    "/{scheduled_transaction_id}", dependencies=[Depends(is_quantum_user)], response_model=ScheduledTransactionRead
)
async def update_scheduled_transaction(
    account_id: int,
    scheduled_transaction_id: int,
    scheduled_transaction: ScheduledTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScheduledTransaction:

    sql = (
        select(ScheduledTransaction)
        .join(Account, ScheduledTransaction.account_id == Account.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_scheduled_transaction = db.exec(sql).one_or_none()

    if not db_scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled transaction not found")

    scheduled_transaction_data = scheduled_transaction.model_dump(exclude_unset=True)

    for key, value in scheduled_transaction_data.items():
        setattr(db_scheduled_transaction, key, value)

    db.add(db_scheduled_transaction)
    db.commit()
    db.refresh(db_scheduled_transaction)

    return db_scheduled_transaction
