from typing import Optional

from sqlmodel import Field, SQLModel


class CategoryBase(SQLModel):
    name: str
    parent_category_id: int = Field(foreign_key="quantum_category.category_id")
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")


class Category(CategoryBase, table=True):
    __tablename__: str = "quantum_category"  # type: ignore

    category_id: Optional[int] = Field(default=None, primary_key=True)


class CategoryCreate(CategoryBase):
    ...


class CategoryRead(CategoryBase):
    category_id: int


class CategoryUpdate(SQLModel):
    ...
