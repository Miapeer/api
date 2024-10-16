from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.models.quantum.transaction_type import (
    TransactionType,
    TransactionTypeCreate,
    TransactionTypeRead,
    TransactionTypeUpdate,
)

router = APIRouter(
    prefix="/transaction-types",
    tags=["Quantum: Transaction Types"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


async def update_transaction_type_id_ref(
    db: DbSession,
    current_user: CurrentActiveUser,
    object_to_update,
    portfolio_id: int,
    transaction_type_id: Optional[int],
    transaction_type_name: Optional[str],
):
    if transaction_type_id is not None:
        transaction_type_sql = (
            select(TransactionType)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(TransactionType.transaction_type_id == transaction_type_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        transaction_type_found = db.exec(transaction_type_sql).first()
        if transaction_type_found:
            object_to_update.transaction_type_id = transaction_type_found.transaction_type_id
        else:
            raise HTTPException(status_code=404, detail="Transaction type not found")
    elif transaction_type_name:
        new_transaction_type = await create_transaction_type(
            db=db,
            current_user=current_user,
            transaction_type=TransactionTypeCreate(portfolio_id=portfolio_id, name=transaction_type_name),
        )
        if new_transaction_type:
            object_to_update.transaction_type_id = new_transaction_type.transaction_type_id
        else:
            raise HTTPException(status_code=500, detail="Could not create transaction type")


@router.get("")
async def get_all_transaction_types(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[TransactionTypeRead]:
    sql = (
        select(TransactionType)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(PortfolioUser.user_id == current_user.user_id)
        .order_by(TransactionType.name)
    )
    transaction_types = db.exec(sql).all()
    return [TransactionTypeRead.model_validate(transaction_type) for transaction_type in transaction_types]


@router.post("")
async def create_transaction_type(
    db: DbSession,
    current_user: CurrentActiveUser,
    transaction_type: TransactionTypeCreate,
) -> TransactionTypeRead:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the transaction type
    db_transaction_type = TransactionType.model_validate(transaction_type)

    db.add(db_transaction_type)
    db.commit()
    db.refresh(db_transaction_type)

    return TransactionTypeRead.model_validate(db_transaction_type)


@router.get("/{transaction_type_id}")
async def get_transaction_type(
    db: DbSession,
    current_user: CurrentActiveUser,
    transaction_type_id: int,
) -> TransactionTypeRead:

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

    return TransactionTypeRead.model_validate(transaction_type)


@router.delete("/{transaction_type_id}")
async def delete_transaction_type(
    db: DbSession,
    current_user: CurrentActiveUser,
    transaction_type_id: int,
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


@router.patch("/{transaction_type_id}")
async def update_transaction_type(
    db: DbSession,
    current_user: CurrentActiveUser,
    transaction_type_id: int,
    transaction_type: TransactionTypeUpdate,
) -> TransactionTypeRead:

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

    if transaction_type.name is not None:
        db_transaction_type.name = transaction_type.name

    db.add(db_transaction_type)
    db.commit()
    db.refresh(db_transaction_type)

    return TransactionTypeRead.model_validate(db_transaction_type)
