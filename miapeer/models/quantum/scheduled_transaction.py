from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel

from miapeer.models.quantum.transaction import TransactionRead


class ScheduledTransactionBase(SQLModel):
    transaction_type_id: Optional[int] = Field(default=None, foreign_key="quantum_transaction_type.transaction_type_id")
    payee_id: Optional[int] = Field(default=None, foreign_key="quantum_payee.payee_id")
    category_id: Optional[int] = Field(default=None, foreign_key="quantum_category.category_id")
    fixed_amount: Optional[int] = None
    estimate_occurrences: Optional[int] = None
    prompt_days: Optional[int] = None
    start_date: date = date.today()
    end_date: Optional[date] = None
    limit_occurrences: Optional[int] = None
    repeat_option_id: Optional[int] = Field(default=None, foreign_key="quantum_repeat_option.repeat_option_id")
    # linked_account_id: int = Field(foreign_key="quantum_account.account_id")
    # linked_account_cycle_end_offset: int
    notes: Optional[str] = None
    on_autopay: bool


class ScheduledTransaction(ScheduledTransactionBase, table=True):
    __tablename__: str = "quantum_scheduled_transaction"  # type: ignore

    scheduled_transaction_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="quantum_account.account_id")

    # account: Account = Relationship(back_populates="scheduled_transactions")
    # transaction_type: TransactionType = Relationship(back_populates="scheduled_transactions")
    # payee: Payee = Relationship(back_populates="scheduled_transactions")
    # category: Category = Relationship(back_populates="scheduled_transactions")
    # repeat_option: RepeatOption = Relationship(back_populates="scheduled_transactions")
    # linked_account: Account = Relationship(back_populates="linked_scheduled_transactions")

    # scheduled_transaction_history: List["ScheduledTransactionHistory"] = Relationship(back_populates="scheduled_transaction")


class ScheduledTransactionCreate(ScheduledTransactionBase):
    transaction_type_name: Optional[str] = None
    payee_name: Optional[str] = None
    category_name: Optional[str] = None


class ScheduledTransactionRead(ScheduledTransactionBase):
    scheduled_transaction_id: int
    account_id: int
    next_transaction: Optional[TransactionRead] = None


class ScheduledTransactionUpdate(SQLModel):
    transaction_type_id: Optional[int] = None
    payee_id: Optional[int] = None
    category_id: Optional[int] = None
    fixed_amount: Optional[int] = None
    estimate_occurrences: Optional[int] = None
    prompt_days: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None
    limit_occurrences: Optional[int] = None
    repeat_option_id: Optional[int] = None
    # linked_account_id: Optional[int]
    # linked_account_cycle_end_offset: Optional[int]
    notes: Optional[str] = None
    on_autopay: bool
