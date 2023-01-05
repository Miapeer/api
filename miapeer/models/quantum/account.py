from typing import Optional

from sqlmodel import Field, SQLModel
from decimal import Decimal


class AccountBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="portfolio.portfolio_id")
    starting_balance: Decimal

class Account(AccountBase, table=True):
    account_id: Optional[int] = Field(default=None, primary_key=True)


class AccountCreate(AccountBase):
    ...


class AccountRead(AccountBase):
    account_id: int


class AccountUpdate(SQLModel):
    ...
