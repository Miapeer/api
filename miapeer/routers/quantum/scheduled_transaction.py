from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
from miapeer.models.quantum.category import Category
from miapeer.models.quantum.payee import Payee
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.repeat_option import RepeatOptionRead
from miapeer.models.quantum.repeat_unit import RepeatUnitRead
from miapeer.models.quantum.scheduled_transaction import (
    ScheduledTransaction,
    ScheduledTransactionCreate,
    ScheduledTransactionRead,
    ScheduledTransactionUpdate,
)
from miapeer.models.quantum.scheduled_transaction_history import (
    ScheduledTransactionHistory,
)
from miapeer.models.quantum.transaction import (
    Transaction,
    TransactionCreate,
    TransactionRead,
)
from miapeer.models.quantum.transaction_type import TransactionType
from miapeer.routers.quantum import repeat_option

router = APIRouter(
    prefix="/accounts/{account_id}/scheduled-transactions",
    tags=["Quantum: Scheduled Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


async def _get_next_transaction(db: DbSession, scheduled_transaction: ScheduledTransaction) -> Optional[TransactionRead]:
    next_transactions = await get_next_iterations(db=db, scheduled_transaction=scheduled_transaction, override_limit=1)

    next_transaction = None
    if next_transactions:
        next_transaction = TransactionRead.model_validate(next_transactions[0].model_dump(), update={"transaction_id": 0})

    return next_transaction


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
        ScheduledTransactionRead.model_validate(
            scheduled_transaction.model_dump(), update={"next_transaction": await _get_next_transaction(db, scheduled_transaction)}
        )
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
    db_scheduled_transaction = ScheduledTransaction.model_validate(scheduled_transaction.model_dump(), update={"account_id": account_id})
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

    return ScheduledTransactionRead.model_validate(
        scheduled_transaction.model_dump(), update={"next_transaction": await _get_next_transaction(db, scheduled_transaction)}
    )


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

    # Do this rather than a `db_refresh` in order to get the next_transaction as well
    updated_scheduled_transaction = await get_scheduled_transaction(db, current_user, account_id, scheduled_transaction_id)

    return updated_scheduled_transaction


async def get_next_iterations(
    db: DbSession, scheduled_transaction: ScheduledTransaction, override_end_date: Optional[date] = None, override_limit: int = 100
):
    MAX_LIMIT = 100
    MAX_END_DATE = date(year=9999, month=1, day=1)

    limit = MAX_LIMIT
    if override_limit and scheduled_transaction.limit_occurrences:
        limit = min(override_limit, scheduled_transaction.limit_occurrences)
    elif override_limit:
        limit = override_limit
    elif scheduled_transaction.limit_occurrences:
        limit = scheduled_transaction.limit_occurrences

    end_date: date = MAX_END_DATE
    if override_end_date and scheduled_transaction.end_date:
        end_date = min(override_end_date, scheduled_transaction.end_date)
    elif override_end_date:
        end_date = override_end_date
    elif scheduled_transaction.end_date:
        end_date = scheduled_transaction.end_date

    # TODO: Use sqlalchemy relationships/backpopulates
    rpt_option: Optional[RepeatOptionRead] = None
    rpt_unit: Optional[RepeatUnitRead] = None

    if scheduled_transaction.repeat_option_id:
        rpt_option = await repeat_option.get_repeat_option(db=db, repeat_option_id=scheduled_transaction.repeat_option_id)

    if rpt_option and rpt_option.repeat_unit_id:
        rpt_unit = await repeat_option.get_repeat_unit(db=db, repeat_unit_id=rpt_option.repeat_unit_id)

    transactions = []
    active_date = scheduled_transaction.start_date

    if rpt_option and rpt_unit:
        while (len(transactions) < limit) and (active_date <= end_date):
            # Special handling for invalid start_dates. Don't add a transaction unless valid.
            if rpt_unit.name != "Semi-Month" or (active_date.day == 1 or active_date.day == 16):
                transactions.append(
                    Transaction.model_validate(
                        scheduled_transaction.model_dump(),
                        update={
                            "transaction_date": active_date,
                            "amount": scheduled_transaction.fixed_amount if scheduled_transaction.fixed_amount else 0,
                        },
                    )
                )

            if rpt_unit.name == "Day":
                active_date += relativedelta(days=rpt_option.quantity)
            elif rpt_unit.name == "Semi-Month":
                if active_date.day < 16:
                    active_date = date(year=active_date.year, month=active_date.month, day=16)
                else:
                    active_date += relativedelta(months=1)
                    active_date = date(year=active_date.year, month=active_date.month, day=1)
            elif rpt_unit.name == "Month":
                active_date += relativedelta(months=rpt_option.quantity)
            elif rpt_unit.name == "Year":
                active_date += relativedelta(years=rpt_option.quantity)
    else:
        transactions.append(
            Transaction.model_validate(
                scheduled_transaction.model_dump(),
                update={"transaction_date": active_date, "amount": scheduled_transaction.fixed_amount if scheduled_transaction.fixed_amount else 0},
            )
        )

    return transactions


@router.post("/{scheduled_transaction_id}/create-transaction")
async def create_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
    override_transaction_data: Optional[TransactionCreate],
) -> TransactionRead:

    scheduled_transaction = await get_scheduled_transaction(
        db=db, current_user=current_user, account_id=account_id, scheduled_transaction_id=scheduled_transaction_id
    )

    if not scheduled_transaction.next_transaction and not override_transaction_data:
        raise HTTPException(status_code=404, detail="No data provided")

    override_data = override_transaction_data.model_dump(exclude_unset=True) if override_transaction_data else {}
    transaction_data = scheduled_transaction.next_transaction.model_dump() if scheduled_transaction.next_transaction else {}

    # Create the transaction
    transaction = Transaction.model_validate(transaction_data, update=override_data)
    db.add(transaction)
    db.commit()  # Need to commit early in order to get the new transaction's ID
    db.refresh(transaction)

    # Link the transaction and scheduled transaction
    link = ScheduledTransactionHistory.model_validate(
        {
            "target_date": scheduled_transaction.start_date,
            "post_date": date.today(),
            "scheduled_transaction_id": scheduled_transaction_id,
            "transaction_id": transaction.transaction_id,
        }
    )
    db.add(link)
    db.commit()

    return TransactionRead.model_validate(transaction)
