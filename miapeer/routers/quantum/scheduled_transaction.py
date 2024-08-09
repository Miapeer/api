from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.scheduled_transaction import (
    ScheduledTransaction,
    ScheduledTransactionCreate,
    ScheduledTransactionRead,
    ScheduledTransactionUpdate,
)
from miapeer.models.quantum.transaction_type import TransactionType

router = APIRouter(
    prefix="/accounts/{account_id}/scheduled-transactions",
    tags=["Quantum: Scheduled Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("")
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


@router.post("")
async def create_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction: ScheduledTransactionCreate,
) -> ScheduledTransactionRead:

    # Get the user's data to verify access
    account_sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    account_found = db.exec(account_sql).first()
    if not account_found:
        raise HTTPException(status_code=404, detail="Account not found")

    if scheduled_transaction.transaction_type_id is not None:
        transaction_type_sql = (
            select(TransactionType)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(TransactionType.transaction_type_id == scheduled_transaction.transaction_type_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        trasaction_type_found = db.exec(transaction_type_sql).first()
        if not trasaction_type_found:
            raise HTTPException(status_code=404, detail="Transaction type not found")

    if scheduled_transaction.payee_id is not None:
        payee_sql = (
            select(Payee)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(Payee.payee_id == scheduled_transaction.payee_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        payee_found = db.exec(payee_sql).first()
        if not payee_found:
            raise HTTPException(status_code=404, detail="Payee not found")

    if scheduled_transaction.category_id is not None:
        category_sql = (
            select(Category)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(Category.category_id == scheduled_transaction.category_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        category_found = db.exec(category_sql).first()
        if not category_found:
            raise HTTPException(status_code=404, detail="Category not found")

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

    scheduled_transaction_sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_scheduled_transaction = db.exec(scheduled_transaction_sql).one_or_none()
    if not db_scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled transaction not found")

    if db_scheduled_transaction.transaction_type_id != scheduled_transaction.transaction_type_id:
        if scheduled_transaction.transaction_type_id:
            transaction_type_sql = (
                select(TransactionType)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(TransactionType.transaction_type_id == scheduled_transaction.transaction_type_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            transaction_type_found = db.exec(transaction_type_sql).one_or_none()
            if transaction_type_found:
                db_scheduled_transaction.transaction_type_id = scheduled_transaction.transaction_type_id
            else:
                raise HTTPException(status_code=404, detail="Transaction type not found")
        else:
            db_scheduled_transaction.transaction_type_id = None

    if db_scheduled_transaction.payee_id != scheduled_transaction.payee_id:
        if scheduled_transaction.payee_id:
            payee_sql = (
                select(Payee)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(Payee.payee_id == scheduled_transaction.payee_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            payee_found = db.exec(payee_sql).one_or_none()
            if payee_found:
                db_scheduled_transaction.payee_id = scheduled_transaction.payee_id
            else:
                raise HTTPException(status_code=404, detail="Payee not found")
        else:
            db_scheduled_transaction.payee_id = None

    if db_scheduled_transaction.category_id != scheduled_transaction.category_id:
        if scheduled_transaction.category_id:
            category_sql = (
                select(Category)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(Category.category_id == scheduled_transaction.category_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            category_found = db.exec(category_sql).one_or_none()
            if category_found:
                db_scheduled_transaction.category_id = scheduled_transaction.category_id
            else:
                raise HTTPException(status_code=404, detail="Category not found")
        else:
            db_scheduled_transaction.category_id = None

    db_scheduled_transaction.fixed_amount = scheduled_transaction.fixed_amount
    db_scheduled_transaction.estimate_occurrences = scheduled_transaction.estimate_occurrences
    db_scheduled_transaction.prompt_days = scheduled_transaction.prompt_days
    db_scheduled_transaction.start_date = scheduled_transaction.start_date
    db_scheduled_transaction.end_date = scheduled_transaction.end_date
    db_scheduled_transaction.limit_occurrences = scheduled_transaction.limit_occurrences
    db_scheduled_transaction.repeat_option_id = scheduled_transaction.repeat_option_id
    db_scheduled_transaction.notes = scheduled_transaction.notes
    db_scheduled_transaction.on_autopay = scheduled_transaction.on_autopay

    db.add(db_scheduled_transaction)
    db.commit()
    db.refresh(db_scheduled_transaction)

    return ScheduledTransactionRead.model_validate(db_scheduled_transaction)
