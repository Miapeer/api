from typing import Optional

from sqlmodel import Field, SQLModel


class AccountBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")


class Account(AccountBase, table=True):
    __tablename__: str = "quantum_account"  # type: ignore

    account_id: Optional[int] = Field(default=None, primary_key=True)


class AccountCreate(AccountBase):
    ...


class AccountRead(AccountBase):
    account_id: int


class AccountUpdate(SQLModel):
    ...
