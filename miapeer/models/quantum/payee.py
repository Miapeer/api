from typing import Optional

from sqlmodel import Field, SQLModel


class PayeeBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")


class Payee(PayeeBase, table=True):
    __tablename__: str = "quantum_payee"  # type: ignore

    payee_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio: Portfolio = Relationship(back_populates="payees")

    # transactions: List["Transaction"] = Relationship(back_populates="payee")
    # scheduled_transactions: List["ScheduledTransaction"] = Relationship(back_populates="payee")
    # import_definitions: List["ImportDefinition"] = Relationship(back_populates="payee")


class PayeeCreate(PayeeBase):
    ...


class PayeeRead(PayeeBase):
    payee_id: int


class PayeeUpdate(SQLModel):
    name: Optional[str]
