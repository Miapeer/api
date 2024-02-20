from typing import Optional

from sqlmodel import Field, SQLModel


class AccountBase(SQLModel):
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")
    name: str
    starting_balance: int


class Account(AccountBase, table=True):
    __tablename__: str = "quantum_account"  # type: ignore

    account_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio: Portfolio = Relationship(back_populates="accounts")

    # transactions: List["Transaction"] = Relationship(back_populates="account")
    # scheduled_transactions: List["ScheduledTransaction"] = Relationship(back_populates="account")
    # linked_scheduled_transactions: List["ScheduledTransaction"] = Relationship(back_populates="linked_account")
    # import_definitions: List["ImportDefinition"] = Relationship(back_populates="account")


class AccountCreate(AccountBase):
    ...


class AccountRead(AccountBase):
    account_id: int
    balance: int  # Calculated


class AccountUpdate(SQLModel):
    name: Optional[str]
    starting_balance: Optional[int]
