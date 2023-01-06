from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_db,
    get_current_active_user,
    is_quantum_user,
    is_quantum_admin,
    is_quantum_super_user,
)
from miapeer.models.quantum.transaction_type import TransactionType, TransactionTypeCreate, TransactionTypeRead, TransactionTypeUpdate
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.miapeer.user import User

router = APIRouter(
    prefix="/transaction-types",
    tags=["Quantum API: Transaction Types"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[TransactionTypeRead])
async def get_all_transaction_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TransactionType]:

    sql = (
        select(TransactionType)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transaction_types = db.exec(sql).all()

    return transaction_types


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=TransactionTypeRead)
async def create_transaction_type(
    transaction_type: TransactionTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionType:

    # Get the user's portfolio
    sql = (
        select(Portfolio)
        .join(PortfolioUser)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the transaction type
    db_transaction_type = TransactionType.from_orm(transaction_type)
    db.add(db_transaction_type)
    db.commit()
    db.refresh(db_transaction_type)

    return db_transaction_type


@router.get("/{transaction_type_id}", dependencies=[Depends(is_quantum_user)], response_model=TransactionType)
async def get_transaction_type(
    transaction_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionType:

    sql = (
        select(TransactionType)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(TransactionType.transaction_type_id == transaction_type_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transaction_type = db.exec(sql).one_or_none()

    if not transaction_type:
        raise HTTPException(status_code=404, detail="Transaction type not found")

    return transaction_type


@router.delete("/{transaction_type_id}", dependencies=[Depends(is_quantum_user)])
def delete_transaction_type(
    transaction_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool]:

    sql = (
        select(TransactionType)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(TransactionType.transaction_type_id == transaction_type_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    transaction_type = db.exec(sql).one_or_none()
    
    if not transaction_type:
        raise HTTPException(status_code=404, detail="Transaction type not found")
    
    db.delete(transaction_type)
    db.commit()

    return {"ok": True}


@router.patch("/{transaction_type_id}", dependencies=[Depends(is_quantum_user)], response_model=TransactionTypeRead)
def update_transaction_type(
    transaction_type_id: int,
    payee: TransactionTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionType:

    sql = (
        select(TransactionType)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(TransactionType.transaction_type_id == transaction_type_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_transaction_type = db.exec(sql).one_or_none()
    
    if not db_transaction_type:
        raise HTTPException(status_code=404, detail="Transaction type not found")

    transaction_type_data = payee.dict(exclude_unset=True)

    for key, value in transaction_type_data.items():
        setattr(db_transaction_type, key, value)

    db.add(db_transaction_type)
    db.commit()
    db.refresh(db_transaction_type)

    return db_transaction_type