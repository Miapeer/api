from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from miapeer.models.quantum.transaction_type import TransactionType

router = APIRouter(
    prefix="/accounts/{account_id}/transactions",
    tags=["Quantum: Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
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


@router.post("/")
async def create_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction: TransactionCreate,
) -> TransactionRead:

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

    if transaction.transaction_type_id is not None:
        transaction_type_sql = (
            select(TransactionType)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(TransactionType.transaction_type_id == transaction.transaction_type_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        trasaction_type_found = db.exec(transaction_type_sql).first()
        if not trasaction_type_found:
            raise HTTPException(status_code=404, detail="Transaction type not found")

    if transaction.payee_id is not None:
        payee_sql = (
            select(Payee)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(Payee.payee_id == transaction.payee_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        payee_found = db.exec(payee_sql).first()
        if not payee_found:
            raise HTTPException(status_code=404, detail="Payee not found")

    if transaction.category_id is not None:
        category_sql = (
            select(Category)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(Category.category_id == transaction.category_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        category_found = db.exec(category_sql).first()
        if not category_found:
            raise HTTPException(status_code=404, detail="Category not found")

    # Create the transaction
    transaction_data = transaction.model_dump()
    transaction_data["account_id"] = account_id
    db_transaction = Transaction.model_validate(transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return TransactionRead.model_validate(db_transaction)


@router.get("/{transaction_id}")
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


@router.delete("/{transaction_id}")
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


@router.patch("/{transaction_id}")
async def update_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    transaction_id: int,
    transaction: TransactionUpdate,
) -> TransactionRead:

    transaction_sql = (
        select(Transaction)
        .join(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(Transaction.transaction_id == transaction_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_transaction = db.exec(transaction_sql).one_or_none()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if db_transaction.transaction_type_id != transaction.transaction_type_id:
        if transaction.transaction_type_id:
            transaction_type_sql = (
                select(TransactionType)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(TransactionType.transaction_type_id == transaction.transaction_type_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            transaction_type_found = db.exec(transaction_type_sql).one_or_none()
            if transaction_type_found:
                db_transaction.transaction_type_id = transaction.transaction_type_id
            else:
                raise HTTPException(status_code=404, detail="Transaction type not found")
        else:
            db_transaction.transaction_type_id = None

    if db_transaction.payee_id != transaction.payee_id:
        if transaction.payee_id:
            payee_sql = (
                select(Payee)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(Payee.payee_id == transaction.payee_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            payee_found = db.exec(payee_sql).one_or_none()
            if payee_found:
                db_transaction.payee_id = transaction.payee_id
            else:
                raise HTTPException(status_code=404, detail="Payee not found")
        else:
            db_transaction.payee_id = None

    if db_transaction.category_id != transaction.category_id:
        if transaction.category_id:
            category_sql = (
                select(Category)
                .join(Portfolio)
                .join(PortfolioUser)
                .where(Category.category_id == transaction.category_id)
                .where(PortfolioUser.user_id == current_user.user_id)
            )
            category_found = db.exec(category_sql).one_or_none()
            if category_found:
                db_transaction.category_id = transaction.category_id
            else:
                raise HTTPException(status_code=404, detail="Category not found")
        else:
            db_transaction.category_id = None

    db_transaction.amount = transaction.amount
    db_transaction.transaction_date = transaction.transaction_date
    db_transaction.clear_date = transaction.clear_date
    db_transaction.check_number = transaction.check_number
    db_transaction.exclude_from_forecast = transaction.exclude_from_forecast
    db_transaction.notes = transaction.notes

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return TransactionRead.model_validate(db_transaction)
