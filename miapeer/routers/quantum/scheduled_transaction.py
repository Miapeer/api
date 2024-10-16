from datetime import date
from enum import Enum
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.account import Account
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
from miapeer.routers.quantum import repeat_option
from miapeer.routers.quantum.category import update_category_id_ref
from miapeer.routers.quantum.payee import update_payee_id_ref
from miapeer.routers.quantum.transaction_type import (
    update_transaction_type_id_ref,
)

router = APIRouter(
    prefix="/accounts/{account_id}/scheduled-transactions",
    tags=["Quantum: Scheduled Transactions"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)

MAX_LIMIT = 100
MAX_END_DATE = date(year=9999, month=1, day=1)


class AmountTrend(Enum):
    FIXED = 0
    STEADY = 1
    AVERAGE = 2


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

    await update_transaction_type_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        transaction_type_id=scheduled_transaction.transaction_type_id,
        transaction_type_name=scheduled_transaction.transaction_type_name,
    )

    await update_payee_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        payee_id=scheduled_transaction.payee_id,
        payee_name=scheduled_transaction.payee_name,
    )

    await update_category_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        category_id=scheduled_transaction.category_id,
        category_name=scheduled_transaction.category_name,
    )

    # Create the scheduled transaction
    db_scheduled_transaction = ScheduledTransaction.model_validate(scheduled_transaction.model_dump(), update={"account_id": account_id})
    db.add(db_scheduled_transaction)
    db.commit()
    db.refresh(db_scheduled_transaction)

    return ScheduledTransactionRead.model_validate(db_scheduled_transaction)


async def _get_scheduled_transaction(db: DbSession, account_id: int, scheduled_transaction_id: int, user_id: int) -> Optional[ScheduledTransaction]:
    sql = (
        select(ScheduledTransaction)
        .join(Account, Account.account_id == ScheduledTransaction.account_id)  # type: ignore
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Account.account_id == account_id)
        .where(ScheduledTransaction.scheduled_transaction_id == scheduled_transaction_id)
        .where(PortfolioUser.user_id == user_id)
    )

    return db.exec(sql).one_or_none()


@router.get("/{scheduled_transaction_id}")
async def get_scheduled_transaction(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
) -> ScheduledTransactionRead:

    scheduled_transaction = await _get_scheduled_transaction(
        db=db, account_id=account_id, scheduled_transaction_id=scheduled_transaction_id, user_id=current_user.user_id if current_user.user_id else 0
    )

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
        object_to_update=db_scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        transaction_type_id=scheduled_transaction.transaction_type_id,
        transaction_type_name=scheduled_transaction.transaction_type_name,
    )

    await update_payee_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        payee_id=scheduled_transaction.payee_id,
        payee_name=scheduled_transaction.payee_name,
    )

    await update_category_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_scheduled_transaction,
        portfolio_id=account_found.portfolio_id,
        category_id=scheduled_transaction.category_id,
        category_name=scheduled_transaction.category_name,
    )

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


def _get_next_iterations_amount_modifier(
    previous_transactions: list[Transaction],
) -> tuple[AmountTrend, int]:
    filtered_transactions = [t for t in previous_transactions if not t.exclude_from_forecast]

    if not filtered_transactions:
        return AmountTrend.FIXED, 0
    elif len(filtered_transactions) == 1:
        return AmountTrend.FIXED, filtered_transactions[0].amount

    deltas: list[int] = []
    for transaction_index, transaction in enumerate(filtered_transactions[:-1]):
        next_transaction = filtered_transactions[transaction_index + 1]
        deltas.append(next_transaction.amount - transaction.amount)

    if all(d == 0 for d in deltas) or all(d > 0 for d in deltas) or all(d < 0 for d in deltas):
        return AmountTrend.STEADY, round(sum(deltas) / len(deltas))
    else:
        return AmountTrend.AVERAGE, round(sum(pt.amount for pt in filtered_transactions) / len(filtered_transactions))


def _get_next_amount(
    previous_amount: int,
    amount_trend: AmountTrend,
    amount_modifier: int,
) -> int:
    if amount_trend == AmountTrend.FIXED:
        return amount_modifier
    elif amount_trend == AmountTrend.STEADY:
        return previous_amount + amount_modifier
    elif amount_trend == AmountTrend.AVERAGE:
        return amount_modifier


async def get_next_iterations(
    db: DbSession,
    scheduled_transaction: ScheduledTransaction | ScheduledTransactionRead,
    override_end_date: Optional[date] = None,
    override_limit: int = MAX_LIMIT,
) -> list[Transaction]:

    if scheduled_transaction.fixed_amount:
        previous_transactions = []
        amount_trend = AmountTrend.FIXED
        amount_modifier = scheduled_transaction.fixed_amount
    else:
        sql = (
            select(Transaction)
            .join(ScheduledTransactionHistory)
            .where(ScheduledTransactionHistory.scheduled_transaction_id == scheduled_transaction.scheduled_transaction_id)
            .order_by(ScheduledTransactionHistory.scheduled_transaction_history_id)  # type: ignore
            .limit(scheduled_transaction.estimate_occurrences)
        )
        previous_transactions = list(db.exec(sql).all())
        amount_trend, amount_modifier = _get_next_iterations_amount_modifier(previous_transactions)

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

    transactions: list[Transaction] = []
    active_date = scheduled_transaction.start_date
    active_amount = previous_transactions[-1].amount if previous_transactions else 0

    if rpt_option and rpt_unit:
        while (len(transactions) < limit) and (active_date <= end_date):
            next_amount = _get_next_amount(previous_amount=active_amount, amount_trend=amount_trend, amount_modifier=amount_modifier)
            active_amount = next_amount

            # Special handling for invalid start_dates. Don't add a transaction unless valid.
            if rpt_unit.name != "Semi-Month" or (active_date.day == 1 or active_date.day == 16):
                transactions.append(
                    Transaction.model_validate(
                        scheduled_transaction.model_dump(),
                        update={
                            "transaction_date": active_date,
                            "amount": next_amount,
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
    override_data["transaction_id"] = None
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

    await progress_iteration(db=db, current_user=current_user, account_id=account_id, scheduled_transaction_id=scheduled_transaction_id)

    return TransactionRead.model_validate(transaction)


@router.post("/{scheduled_transaction_id}/skip-iteration")
async def progress_iteration(
    db: DbSession,
    current_user: CurrentActiveUser,
    account_id: int,
    scheduled_transaction_id: int,
) -> None:

    scheduled_transaction = await _get_scheduled_transaction(
        db=db, user_id=current_user.user_id if current_user.user_id else 0, account_id=account_id, scheduled_transaction_id=scheduled_transaction_id
    )

    if not scheduled_transaction:
        raise HTTPException(status_code=404, detail="Scheduled Transaction not found")

    # Update scheduled transaction's next iteration date by getting the next two iterations (actual current, actual next)
    next_iterations = await get_next_iterations(db=db, scheduled_transaction=scheduled_transaction, override_limit=2)

    scheduled_transaction.start_date = next_iterations[1].transaction_date if len(next_iterations) == 2 else MAX_END_DATE
    db.add(scheduled_transaction)
    db.commit()
