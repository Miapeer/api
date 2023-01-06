from typing import Optional

from sqlmodel import Field, SQLModel
from decimal import Decimal
from datetime import date


class ScheduledTransactionHistoryBase(SQLModel):
    target_date: date
    post_date: date
    scheduled_transaction_id: int = Field(foreign_key="scheduled_transaction.scheduled_transaction_id")
    transaction_id: int = Field(foreign_key="transaction.transaction_id")

class ScheduledTransactionHistory(ScheduledTransactionHistoryBase, table=True):
    scheduled_transaction_history_id: Optional[int] = Field(default=None, primary_key=True)


class ScheduledTransactionHistoryCreate(ScheduledTransactionHistoryBase):
    ...


class ScheduledTransactionHistoryRead(ScheduledTransactionHistoryBase):
    scheduled_transaction_history_id: int


class ScheduledTransactionHistoryUpdate(SQLModel):
    ...
