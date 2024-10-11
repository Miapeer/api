from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import CurrentActiveUser, DbSession, is_quantum_user
from miapeer.models.quantum.category import (
    Category,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)
from miapeer.models.quantum.portfolio import Portfolio
from miapeer.models.quantum.portfolio_user import PortfolioUser

router = APIRouter(
    prefix="/categories",
    tags=["Quantum: Categories"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


async def update_category_id_ref(
    db: DbSession, current_user: CurrentActiveUser, object_to_update, portfolio_id: int, category_id: Optional[int], category_name: Optional[str]
):
    if category_id is not None:
        category_sql = (
            select(Category)
            .join(Portfolio)
            .join(PortfolioUser)
            .where(Category.category_id == category_id)
            .where(PortfolioUser.user_id == current_user.user_id)
        )
        category_found = db.exec(category_sql).first()
        if category_found:
            object_to_update.category_id = category_found.category_id
        else:
            raise HTTPException(status_code=404, detail="Category not found")
    elif category_name:
        new_category = await create_category(db=db, current_user=current_user, category=CategoryCreate(portfolio_id=portfolio_id, name=category_name))
        if new_category:
            object_to_update.category_id = new_category.category_id
        else:
            raise HTTPException(status_code=500, detail="Could not create category")


@router.get("")
async def get_all_categories(
    db: DbSession,
    current_user: CurrentActiveUser,
) -> list[CategoryRead]:
    sql = select(Category).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id).order_by(Category.name)
    categories = db.exec(sql).all()
    return [CategoryRead.model_validate(category) for category in categories]


@router.post("")
async def create_category(
    db: DbSession,
    current_user: CurrentActiveUser,
    category: CategoryCreate,
) -> CategoryRead:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the category
    db_category = Category.model_validate(category)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return CategoryRead.model_validate(db_category)


@router.get("/{category_id}")
async def get_category(
    db: DbSession,
    current_user: CurrentActiveUser,
    category_id: int,
) -> CategoryRead:

    sql = (
        select(Category)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Category.category_id == category_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    category = db.exec(sql).one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return CategoryRead.model_validate(category)


@router.delete("/{category_id}")
async def delete_category(
    db: DbSession,
    current_user: CurrentActiveUser,
    category_id: int,
) -> dict[str, bool]:

    sql = (
        select(Category)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Category.category_id == category_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    category = db.exec(sql).one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    return {"ok": True}


@router.patch("/{category_id}")
async def update_category(
    db: DbSession,
    current_user: CurrentActiveUser,
    category_id: int,
    category: CategoryUpdate,
) -> CategoryRead:

    sql = (
        select(Category)
        .join(Portfolio)
        .join(PortfolioUser)
        .where(Category.category_id == category_id)
        .where(PortfolioUser.user_id == current_user.user_id)
    )
    db_category = db.exec(sql).one_or_none()

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.name is not None:
        db_category.name = category.name

    db_category.parent_category_id = category.parent_category_id

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return CategoryRead.model_validate(db_category)
