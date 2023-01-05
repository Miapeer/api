from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionTypeBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="portfolio.portfolio_id")

class TransactionType(TransactionTypeBase, table=True):
    transaction_type_id: Optional[int] = Field(default=None, primary_key=True)


class TransactionTypeCreate(TransactionTypeBase):
    ...


class TransactionTypeRead(TransactionTypeBase):
    transaction_type_id: int


class TransactionTypeUpdate(SQLModel):
    ...
