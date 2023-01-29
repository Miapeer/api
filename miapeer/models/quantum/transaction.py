from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    name: str
    transaction_type_id: int = Field(foreign_key="quantum_transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="quantum_payee.payee_id")
    category_id: int = Field(foreign_key="quantum_category.category_id")
    amount: Decimal
    transaction_date: date
    clear_date: date
    check_number: int
    exclude_from_forecast: bool
    notes: str


class Transaction(TransactionBase, table=True):
    __tablename__: str = "quantum_transaction"  # type: ignore

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="quantum_account.account_id")


class TransactionCreate(TransactionBase):
    ...


class TransactionRead(TransactionBase):
    transaction_id: int
    account_id: int


class TransactionUpdate(SQLModel):
    ...
