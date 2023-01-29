from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_current_active_user,
    get_db,
    is_quantum_user,
)
from miapeer.models.miapeer.user import User
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
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_quantum_user)], response_model=list[CategoryRead])
async def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Category]:

    sql = select(Category).join(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    categories = db.exec(sql).all()

    return categories


@router.post("/", dependencies=[Depends(is_quantum_user)], response_model=CategoryRead)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Category:

    # Get the user's portfolio
    sql = select(Portfolio).join(PortfolioUser).where(PortfolioUser.user_id == current_user.user_id)
    portfolio = db.exec(sql).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Create the category
    db_category = Category.from_orm(category)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category


@router.get("/{category_id}", dependencies=[Depends(is_quantum_user)], response_model=Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Category:

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

    return category


@router.delete("/{category_id}", dependencies=[Depends(is_quantum_user)])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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


@router.patch("/{category_id}", dependencies=[Depends(is_quantum_user)], response_model=CategoryRead)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Category:

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

    category_data = category.dict(exclude_unset=True)

    for key, value in category_data.items():
        setattr(db_category, key, value)

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category
