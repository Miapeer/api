from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    transaction_type_id: int = Field(foreign_key="quantum_transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="quantum_payee.payee_id")
    category_id: int = Field(foreign_key="quantum_category.category_id")
    amount: int
    transaction_date: date
    clear_date: date
    check_number: int
    exclude_from_forecast: bool
    notes: str


class Transaction(TransactionBase, table=True):
    __tablename__: str = "quantum_transaction"  # type: ignore

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="quantum_account.account_id")

    # account: Account = Relationship(back_populates="transactions")
    # transaction_type: TransactionType = Relationship(back_populates="transactions")
    # payee: Payee = Relationship(back_populates="transactions")
    # category: Category = Relationship(back_populates="transactions")

    # scheduled_transaction_history: List["ScheduledTransactionHistory"] = Relationship(back_populates="scheduled_transaction")


class TransactionCreate(TransactionBase):
    ...


class TransactionRead(TransactionBase):
    transaction_id: int
    account_id: int


class TransactionUpdate(SQLModel):
    transaction_type_id: Optional[int]
    payee_id: Optional[int]
    category_id: Optional[int]
    amount: Optional[int]
    transaction_date: Optional[date]
    clear_date: Optional[date]
    check_number: Optional[int]
    exclude_from_forecast: Optional[bool]
    notes: Optional[str]
