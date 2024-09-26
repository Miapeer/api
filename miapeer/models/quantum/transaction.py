from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    # parent_category_id: Optional[int] = Field(default=None, foreign_key="quantum_category.category_id")

    transaction_type_id: Optional[int] = Field(default=None, foreign_key="quantum_transaction_type.transaction_type_id")
    payee_id: Optional[int] = Field(default=None, foreign_key="quantum_payee.payee_id")
    category_id: Optional[int] = Field(default=None, foreign_key="quantum_category.category_id")
    amount: int = 0
    transaction_date: date = date.today()
    clear_date: Optional[date] = None
    check_number: Optional[str] = None
    exclude_from_forecast: bool = False
    notes: Optional[str] = None


class Transaction(TransactionBase, table=True):
    __tablename__: str = "quantum_transaction"  # type: ignore

    account_id: Optional[int] = Field(default=None, foreign_key="quantum_account.account_id")
    transaction_id: Optional[int] = Field(default=None, primary_key=True)

    # account: Account = Relationship(back_populates="transactions")
    # transaction_type: TransactionType = Relationship(back_populates="transactions")
    # payee: Payee = Relationship(back_populates="transactions")
    # category: Category = Relationship(back_populates="transactions")

    # scheduled_transaction_history: List["ScheduledTransactionHistory"] = Relationship(back_populates="scheduled_transaction")


class TransactionCreate(TransactionBase):
    transaction_type_name: Optional[str] = None
    payee_name: Optional[str] = None
    category_name: Optional[str] = None


class TransactionRead(TransactionBase):
    transaction_id: int
    account_id: int
    balance: Optional[int] = None
    forecast_from_scheduled_transaction_id: Optional[int] = None


class TransactionUpdate(SQLModel):
    transaction_type_id: Optional[int] = None
    transaction_type_name: Optional[str] = None
    payee_id: Optional[int] = None
    payee_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    amount: int
    transaction_date: date
    clear_date: Optional[date] = None
    check_number: Optional[str] = None
    exclude_from_forecast: bool
    notes: Optional[str] = None
