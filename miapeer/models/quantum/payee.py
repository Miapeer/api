from typing import Optional

from sqlmodel import Field, SQLModel


class PayeeBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="portfolio.portfolio_id")

class Payee(PayeeBase, table=True):
    payee_id: Optional[int] = Field(default=None, primary_key=True)


class PayeeCreate(PayeeBase):
    ...


class PayeeRead(PayeeBase):
    payee_id: int


class PayeeUpdate(SQLModel):
    ...
