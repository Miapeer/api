from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.adapter.sql import budget as budget_sql
from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.budget import (
    Budget,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser
from miapeer.routers.quantum.category import update_category_id_ref

router = APIRouter(
    prefix="/budgets",
    tags=["Quantum: Budgets"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


def get_budget_balances(db: DbSession, current_user: CurrentActiveUser, budget: Optional[Budget] = None) -> int:
    limit_date = date(year=date.today().year, month=date.today().month, day=1)
    limit_date -= relativedelta(years=1)

    if budget is None:
        data = db.exec(
            budget_sql.GET_ALL,  # type: ignore
            params={
                "user_id": current_user.user_id,
                "limit_date": limit_date,
            },
        ).all()
    else:
        data = db.exec(
            budget_sql.GET_ONE,  # type: ignore
            params={
                "budget_id": budget.budget_id,
                "user_id": current_user.user_id,
                "limit_date": limit_date,
            },
        ).all()

    return data


@router.get("")
async def get_all_budgets(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[BudgetRead]:
    sql = select(Budget).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    budgets = db.exec(sql).all()

    return [BudgetRead.model_validate(budget.model_dump(), update={"data": get_budget_balances(db, current_user, budget)}) for budget in budgets]


@router.post("")
async def create_budget(
    db: DbSession,
    current_user: CurrentActiveUser,
    budget: BudgetCreate,
) -> BudgetRead:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the budget
    db_budget = Budget.model_validate(budget)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)

    budget_balance = get_budget_balances(db, current_user, db_budget)
    return BudgetRead.model_validate(db_budget.model_dump(), update={"data": budget_balance})


@router.get("/{budget_id}")
async def get_budget(
    db: DbSession,
    current_user: CurrentActiveUser,
    budget_id: int,
) -> BudgetRead:

    sql = select(Budget).join(Portfolio).join(PortfolioUser).where(Budget.budget_id == budget_id).where(PortfolioUser.user_id == current_user.user_id)
    budget = db.exec(sql).one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    budget_balance = get_budget_balances(db, current_user, budget)

    return BudgetRead.model_validate(budget.model_dump(), update={"data": budget_balance})


@router.delete("/{budget_id}")
async def delete_budget(
    db: DbSession,
    current_user: CurrentActiveUser,
    budget_id: int,
) -> dict[str, bool]:

    sql = select(Budget).join(Portfolio).join(PortfolioUser).where(Budget.budget_id == budget_id).where(PortfolioUser.user_id == current_user.user_id)
    budget = db.exec(sql).one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(budget)
    db.commit()

    return {"ok": True}


@router.patch("/{budget_id}")
async def update_budget(
    db: DbSession,
    current_user: CurrentActiveUser,
    budget_id: int,
    budget: BudgetUpdate,
) -> BudgetRead:

    sql = select(Budget).join(Portfolio).join(PortfolioUser).where(Budget.budget_id == budget_id).where(PortfolioUser.user_id == current_user.user_id)
    db_budget = db.exec(sql).one_or_none()

    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    await update_category_id_ref(
        db=db,
        current_user=current_user,
        object_to_update=db_budget,
        portfolio_id=db_budget.portfolio_id,
        category_id=budget.category_id,
        category_name=budget.category_name,
    )

    if budget.name is not None:
        db_budget.name = budget.name

    if budget.amount is not None:
        db_budget.amount = budget.amount

    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)

    budget_balance = get_budget_balances(db, current_user, db_budget)
    return BudgetRead.model_validate(db_budget.model_dump(), update={"data": budget_balance})
