from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_current_active_user,
    get_db,
    is_quantum_super_user,
    is_quantum_user,
)
from miapeer.models.miapeer.user import User
from miapeer.models.quantum.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioRead,
    PortfolioUpdate,
)
from miapeer.models.quantum.portfolio_user import PortfolioUser

router = APIRouter(
    prefix="/portfolios",
    tags=["Quantum: Portfolios"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[PortfolioRead])
async def get_all_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Portfolio]:

    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolios = db.exec(sql).all()

    return portfolios


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=PortfolioRead)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Portfolio:

    # Create the portfolio
    db_portfolio = Portfolio.from_orm(portfolio)
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    # Assign the current user to the portfolio
    new_portfolio_user = PortfolioUser(portfolio_id=db_portfolio.portfolio_id, user_id=current_user.user_id)
    db.add(new_portfolio_user)
    db.commit()

    return db_portfolio


@router.get("/{portfolio_id}", dependencies=[Depends(is_quantum_user)], response_model=Portfolio)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Portfolio:

    sql = (
        select(Portfolio)
        .join(PortfolioUser)
        .where(Portfolio.portfolio_id == portfolio_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    portfolio = db.exec(sql).one_or_none()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return portfolio


@router.delete("/{portfolio_id}", dependencies=[Depends(is_quantum_super_user)])
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    portfolio = db.get(Portfolio, portfolio_id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.delete(portfolio)
    db.commit()

    return {"ok": True}


@router.patch("/{portfolio_id}", dependencies=[Depends(is_quantum_super_user)], response_model=PortfolioRead)
def update_portfolio(
    portfolio_id: int,
    portfolio: PortfolioUpdate,
    db: Session = Depends(get_db),
) -> Portfolio:

    db_portfolio = db.get(Portfolio, portfolio_id)

    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    portfolio_data = portfolio.dict(exclude_unset=True)

    for key, value in portfolio_data.items():
        setattr(db_portfolio, key, value)

    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    return db_portfolio
