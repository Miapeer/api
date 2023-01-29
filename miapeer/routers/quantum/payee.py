from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_current_active_user,
    get_db,
    is_quantum_user,
)
from miapeer.models.miapeer.user import User
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
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[PayeeRead])
async def get_all_payees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Payee]:

    sql = select(Payee).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    payees = db.exec(sql).all()

    return payees


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=PayeeRead)
async def create_payee(
    payee: PayeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Payee:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the payee
    db_payee = Payee.from_orm(payee)
    db.add(db_payee)
    db.commit()
    db.refresh(db_payee)

    return db_payee


@router.get("/{payee_id}", dependencies=[Depends(is_quantum_user)], response_model=Payee)
async def get_payee(
    payee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Payee:

    sql = (
        select(Payee)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Payee.payee_id == payee_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    payee = db.exec(sql).one_or_none()

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    return payee


@router.delete("/{payee_id}", dependencies=[Depends(is_quantum_user)])
def delete_payee(
    payee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool]:

    sql = (
        select(Payee)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Payee.payee_id == payee_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    payee = db.exec(sql).one_or_none()

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    db.delete(payee)
    db.commit()

    return {"ok": True}


@router.patch("/{payee_id}", dependencies=[Depends(is_quantum_user)], response_model=PayeeRead)
def update_payee(
    payee_id: int,
    payee: PayeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Payee:

    sql = (
        select(Payee)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Payee.payee_id == payee_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_payee = db.exec(sql).one_or_none()

    if not db_payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    payee_data = payee.dict(exclude_unset=True)

    for key, value in payee_data.items():
        setattr(db_payee, key, value)

    db.add(db_payee)
    db.commit()
    db.refresh(db_payee)

    return db_payee
