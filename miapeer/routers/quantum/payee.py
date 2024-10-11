from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.payee import (
    Payee,
    PayeeCreate,
    PayeeRead,
    PayeeUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser

router = APIRouter(
    prefix="/payees",
    tags=["Quantum: Payees"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


async def update_payee_id_ref(
    db: DbSession, current_user: CurrentActiveUser, object_to_update, portfolio_id: int, payee_id: Optional[int], payee_name: Optional[str]
):
    if payee_id is not None:
        payee_sql = (
            select(Payee).join(Portfolio).join(PortfolioUser).where(Payee.payee_id == payee_id).where(PortfolioUser.user_id == current_user.user_id)
        )
        payee_found = db.exec(payee_sql).first()
        if payee_found:
            object_to_update.payee_id = payee_found.payee_id
        else:
            raise HTTPException(status_code=404, detail="Payee not found")
    elif payee_name:
        new_payee = await create_payee(db=db, current_user=current_user, payee=PayeeCreate(portfolio_id=portfolio_id, name=payee_name))
        if new_payee:
            object_to_update.payee_id = new_payee.payee_id
        else:
            raise HTTPException(status_code=500, detail="Could not create payee")


@router.get("")
async def get_all_payees(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[PayeeRead]:
    sql = select(Payee).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id).order_by(Payee.name)
    payees = db.exec(sql).all()
    return [PayeeRead.model_validate(payee) for payee in payees]


@router.post("")
async def create_payee(
    db: DbSession,
    current_user: CurrentActiveUser,
    payee: PayeeCreate,
) -> PayeeRead:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the payee
    db_payee = Payee.model_validate(payee)
    db.add(db_payee)
    db.commit()
    db.refresh(db_payee)

    return PayeeRead.model_validate(db_payee)


@router.get("/{payee_id}")
async def get_payee(
    db: DbSession,
    current_user: CurrentActiveUser,
    payee_id: int,
) -> PayeeRead:

    sql = select(Payee).join(Portfolio).join(PortfolioUser).where(Payee.payee_id == payee_id).where(PortfolioUser.user_id == current_user.user_id)
    payee = db.exec(sql).one_or_none()

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    return PayeeRead.model_validate(payee)


@router.delete("/{payee_id}")
async def delete_payee(
    db: DbSession,
    current_user: CurrentActiveUser,
    payee_id: int,
) -> dict[str, bool]:

    sql = select(Payee).join(Portfolio).join(PortfolioUser).where(Payee.payee_id == payee_id).where(PortfolioUser.user_id == current_user.user_id)
    payee = db.exec(sql).one_or_none()

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    db.delete(payee)
    db.commit()

    return {"ok": True}


@router.patch("/{payee_id}")
async def update_payee(
    db: DbSession,
    current_user: CurrentActiveUser,
    payee_id: int,
    payee: PayeeUpdate,
) -> PayeeRead:

    sql = select(Payee).join(Portfolio).join(PortfolioUser).where(Payee.payee_id == payee_id).where(PortfolioUser.user_id == current_user.user_id)
    db_payee = db.exec(sql).one_or_none()

    if not db_payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    if payee.name is not None:
        db_payee.name = payee.name

    db.add(db_payee)
    db.commit()
    db.refresh(db_payee)

    return PayeeRead.model_validate(db_payee)
