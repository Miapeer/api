from typing import Optional

from sqlmodel import Field, SQLModel


class BudgetBase(SQLModel):
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")
    category_id: int = Field(default=None, foreign_key="quantum_category.category_id")
    name: str
    amount: int


class Budget(BudgetBase, table=True):
    __tablename__: str = "quantum_budget"  # type: ignore

    budget_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio: Portfolio = Relationship(back_populates="categories")


class BudgetCreate(BudgetBase):
    ...


class BudgetRead(BudgetBase):
    budget_id: int
    data: list[tuple[str, int]]


class BudgetUpdate(SQLModel):
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    name: Optional[str] = None
    amount: Optional[int] = None
