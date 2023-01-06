from typing import Optional

from sqlmodel import Field, SQLModel
from decimal import Decimal
from datetime import date


class TransactionBase(SQLModel):
    name: str
    transaction_type_id: int = Field(foreign_key="transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="payee.payee_id")
    category_id: int = Field(foreign_key="category.category_id")
    amount: Decimal
    transaction_date: date
    clear_date: date
    check_number: int
    exclude_from_forecast: bool
    notes: str

class Transaction(TransactionBase, table=True):
    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.account_id")

class TransactionCreate(TransactionBase):
    ...


class TransactionRead(TransactionBase):
    transaction_id: int
    account_id: int


class TransactionUpdate(SQLModel):
    ...
