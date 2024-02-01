from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

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

router = APIRouter(
    prefix="/accounts",
    tags=["Quantum: Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)])
async def get_all_accounts(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[AccountRead]:
    sql = select(Account).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    accounts = db.exec(sql).all()
    return [AccountRead.model_validate(account) for account in accounts]


@router.post("/", dependencies=[Depends(is_quantum_user)])
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

    initial_transaction = Transaction(
        transaction_type_id=-1,
        payee_id=None,
        category_id=None,
        amount=account.starting_balance,
        transaction_date=date.today(),
        clear_date=date.today(),
        check_number=None,
        exclude_from_forecast=True,
        notes=None,
    )

    db.add(initial_transaction)
    db.commit()

    return AccountRead.model_validate(db_account)


@router.get("/{account_id}", dependencies=[Depends(is_quantum_user)])
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

    return AccountRead.model_validate(account)


@router.delete("/{account_id}", dependencies=[Depends(is_quantum_user)])
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


@router.patch("/{account_id}", dependencies=[Depends(is_quantum_user)])
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

    updated_account = Account.model_validate(db_account.model_dump(), update=account.model_dump())

    db.add(updated_account)
    db.commit()
    db.refresh(updated_account)

    return AccountRead.model_validate(updated_account)
