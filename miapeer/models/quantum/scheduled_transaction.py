from typing import Optional

from sqlmodel import Field, SQLModel
from decimal import Decimal
from datetime import date


class ScheduledTransactionBase(SQLModel):
    name: str
    transaction_type_id: int = Field(foreign_key="transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="payee.payee_id")
    category_id: int = Field(foreign_key="category.category_id")
    fixed_amount: Decimal
    estimate_occurrences: int
    prompt_days: int
    start_date: date
    end_date: date
    limit_occurrences: int
    repeat_option_id: int = Field(foreign_key="repeat_option.repeat_option_id")
    linked_account_id: int = Field(foreign_key="account.account_id")
    linked_account_cycle_end_offset: int
    notes: str
    on_autopay: bool


class ScheduledTransaction(ScheduledTransactionBase, table=True):
    scheduled_transaction_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.account_id")


class ScheduledTransactionCreate(ScheduledTransactionBase):
    ...


class ScheduledTransactionRead(ScheduledTransactionBase):
    scheduled_transaction_id: int
    account_id: int


class ScheduledTransactionUpdate(SQLModel):
    ...
