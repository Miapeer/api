from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionSummaryBase(SQLModel):
    account_id: int = Field(foreign_key="quantum_account.account_id")
    year: int
    month: int
    balance: int


class TransactionSummary(TransactionSummaryBase, table=True):
    __tablename__: str = "quantum_transaction_summary"  # type: ignore

    transaction_summary_id: Optional[int] = Field(default=None, primary_key=True)


class TransactionSummaryCreate(TransactionSummaryBase):
    ...


class TransactionSummaryRead(TransactionSummaryBase):
    ...
