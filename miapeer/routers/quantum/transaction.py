from datetime import date

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.adapter.sql import transaction as transaction_sql
from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.scheduled_transaction_history import (
    ScheduledTransactionHistory,
)
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from miapeer.routers.quantum import scheduled_transaction
from miapeer.routers.quantum.category import update_category_id_ref
from miapeer.routers.quantum.payee import update_payee_id_ref
from miapeer.routers.quantum.transaction_type import (
    update_transaction_type_id_ref,
)

router = APIRouter(
    prefix="/accounts/{account_id}/transactions",
    tags=["Quantum: Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


async def _get_forecasted_transactions(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    limit_forecast_date: date,
) -> list[TransactionRead]:
    scheduled_transactions = await scheduled_transaction.get_all_scheduled_transactions(db=db, current_user=current_user, account_id=account_id)

    forecasted_transactions: list[TransactionRead] = []
    for st in scheduled_transactions:
        fts = await scheduled_transaction.get_next_iterations(db=db, scheduled_transaction=st, override_end_date=limit_forecast_date)

        for ft in fts:
            forecasted_transactions.append(
                TransactionRead.model_validate(
                    ft.model_dump(),
                    update={
                        "transaction_id": 0,
                        "forecast_from_scheduled_transaction_id": st.scheduled_transaction_id,
                    },
                )
            )

    return forecasted_transactions


def _merge_transactions_with_forecast(transactions: list[TransactionRead], forecasted_transactions: list[TransactionRead]):
    if not forecasted_transactions:
        # Shortcut if there's nothing to merge
        return transactions

    if not transactions:
        # Shortcut if there's nothing to merge
        return forecasted_transactions

    merged_transactions: list[TransactionRead] = []

    forecasted_transactions.sort(key=lambda x: x.transaction_date)

    transaction_index = 0
    forecast_index = 0
    while transaction_index < len(transactions) and forecast_index < len(forecasted_transactions):
        if (
            transactions[transaction_index].clear_date
            or transactions[transaction_index].transaction_date <= forecasted_transactions[forecast_index].transaction_date
        ):
            merged_transactions.append(transactions[transaction_index])
            transaction_index += 1
        else:
            merged_transactions.append(forecasted_transactions[forecast_index])
            forecast_index += 1

    if transaction_index < len(transactions):
        merged_transactions.extend(transactions[transaction_index:])

    if forecast_index < len(forecasted_transactions):
        merged_transactions.extend(forecasted_transactions[forecast_index:])

    return merged_transactions


@router.get("")
async def get_all_transactions(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    limit_months: int = 3,
    limit_forecast_months: int = 1,
) -> list[TransactionRead]:
    limit_months = max(limit_months, 0)
    limit_date = date(year=date.today().year, month=date.today().month, day=1)
    limit_date -= relativedelta(months=limit_months)

    limit_forecast_months = max(limit_forecast_months, 0)
    limit_forecast_date = date.today()
    limit_forecast_date += relativedelta(months=limit_forecast_months)

    transactions = db.exec(
        transaction_sql.GET_ALL,  # type: ignore
        params={
            "account_id": account_id,
            "user_id": current_user.user_id,
            "limit_date": limit_date,
        },
    ).all()

    # TODO: Currently operating off of "magic" transactions. The SQL produces order_index=-2 as the starting balance of the account and
    #           order_index=-1 as all transactions before the reporting period. This should be reviewed again later.

    running_balance: int = sum([t.amount for t in transactions if t.order_index <= 0])

    actual_transactions = [TransactionRead.model_validate(t) for t in transactions if t.order_index > 0]
    forecasted_transactions = await _get_forecasted_transactions(
        db=db,
        current_user=current_user,
        account_id=account_id,
        limit_forecast_date=limit_forecast_date,
    )
    merged_transactions = _merge_transactions_with_forecast(
        transactions=actual_transactions,
        forecasted_transactions=forecasted_transactions,
    )

    for t in merged_transactions:
        running_balance += t.amount
        t.balance = running_balance

    return merged_transactions


@router.post("")
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

    await update_transaction_type_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=transaction,
        portfolio_id=account_found.portfolio_id,
        transaction_type_id=transaction.transaction_type_id,
        transaction_type_name=transaction.transaction_type_name,
    )

    await update_payee_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=transaction,
        portfolio_id=account_found.portfolio_id,
        payee_id=transaction.payee_id,
        payee_name=transaction.payee_name,
    )

    await update_category_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=transaction,
        portfolio_id=account_found.portfolio_id,
        category_id=transaction.category_id,
        category_name=transaction.category_name,
    )

    # Create the transaction
    db_transaction = Transaction.model_validate(transaction.model_dump(), update={"account_id": account_id})
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

    sql = select(ScheduledTransactionHistory).where(ScheduledTransactionHistory.transaction_id == transaction_id)
    scheduled_transaction_history = db.exec(sql).one_or_none()

    if scheduled_transaction_history:
        db.delete(scheduled_transaction_history)

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

    await update_transaction_type_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_transaction,
        portfolio_id=account_found.portfolio_id,
        transaction_type_id=transaction.transaction_type_id,
        transaction_type_name=transaction.transaction_type_name,
    )

    await update_payee_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_transaction,
        portfolio_id=account_found.portfolio_id,
        payee_id=transaction.payee_id,
        payee_name=transaction.payee_name,
    )

    await update_category_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_transaction,
        portfolio_id=account_found.portfolio_id,
        category_id=transaction.category_id,
        category_name=transaction.category_name,
    )

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
