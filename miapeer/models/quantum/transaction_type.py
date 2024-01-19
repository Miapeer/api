from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionTypeBase(SQLModel):
    name: str
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")


class TransactionType(TransactionTypeBase, table=True):
    __tablename__: str = "quantum_transaction_type"  # type: ignore

    transaction_type_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio: Portfolio = Relationship(back_populates="transaction_types")

    # transactions: List["Transaction"] = Relationship(back_populates="transaction_type")
    # scheduled_transactions: List["ScheduledTransaction"] = Relationship(back_populates="transaction_type")
    # import_definitions: List["ImportDefinition"] = Relationship(back_populates="transaction_type")


class TransactionTypeCreate(TransactionTypeBase):
    ...


class TransactionTypeRead(TransactionTypeBase):
    transaction_type_id: int


class TransactionTypeUpdate(SQLModel):
    name: Optional[str]
