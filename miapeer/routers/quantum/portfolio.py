from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import (
    CurrentActiveUser,
    DbSession,
    is_quantum_super_user,
    is_quantum_user,
)
from miapeer.models.quantum.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioRead,
)
from miapeer.models.quantum.portfolio_user import PortfolioUser

router = APIRouter(
    prefix="/portfolios",
    tags=["Quantum: Portfolios"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)])
async def get_all_portfolios(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[PortfolioRead]:
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolios = db.exec(sql).all()
    return [PortfolioRead.model_validate(portfolio) for portfolio in portfolios]


@router.post("/", dependencies=[Depends(is_quantum_user)])
async def create_portfolio(
    db: DbSession,
    current_user: CurrentActiveUser,
    portfolio: PortfolioCreate,
) -> PortfolioRead:

    # Create the portfolio
    db_portfolio = Portfolio.model_validate(portfolio)
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    # Assign the current user to the portfolio
    new_portfolio_user = PortfolioUser(portfolio_id=db_portfolio.portfolio_id, user_id=current_user.user_id)
    db.add(new_portfolio_user)
    db.commit()

    return PortfolioRead.model_validate(db_portfolio)


@router.get("/{portfolio_id}", dependencies=[Depends(is_quantum_user)])
async def get_portfolio(
    db: DbSession,
    current_user: CurrentActiveUser,
    portfolio_id: int,
) -> PortfolioRead:

    sql = (
        select(Portfolio)
        .join(PortfolioUser)
        .where(Portfolio.portfolio_id == portfolio_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    portfolio = db.exec(sql).one_or_none()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return PortfolioRead.model_validate(portfolio)


@router.delete("/{portfolio_id}", dependencies=[Depends(is_quantum_super_user)])
async def delete_portfolio(db: DbSession, portfolio_id: int) -> dict[str, bool]:
    portfolio = db.get(Portfolio, portfolio_id)

    sql = select(PortfolioUser).where(PortfolioUser.portfolio_id == portfolio_id)
    portfolio_users = db.exec(sql).all()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.delete(portfolio)
    for portfolio_user in portfolio_users:
        db.delete(portfolio_user)

    db.commit()

    return {"ok": True}
