from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_db,
    get_current_active_user,
    is_quantum_user,
    is_quantum_admin,
    is_quantum_super_user,
)
from miapeer.models.quantum.account import Account, AccountCreate, AccountRead, AccountUpdate
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.miapeer.user import User

router = APIRouter(
    prefix="/accounts",
    tags=["Quantum API: Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[AccountRead])
async def get_all_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Account]:

    sql = (
        select(Account)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    accounts = db.exec(sql).all()

    return accounts


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=AccountRead)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Account:

    # Get the user's portfolio
    sql = (
        select(Portfolio)
        .join(PortfolioUser)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the account
    db_account = Account.from_orm(account)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account


@router.get("/{account_id}", dependencies=[Depends(is_quantum_user)], response_model=Account)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Account:

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

    return account


@router.delete("/{account_id}", dependencies=[Depends(is_quantum_user)])
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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


@router.patch("/{account_id}", dependencies=[Depends(is_quantum_user)], response_model=AccountRead)
def update_account(
    account_id: int,
    account: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Account:

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

    account_data = account.dict(exclude_unset=True)

    for key, value in account_data.items():
        setattr(db_account, key, value)

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account
