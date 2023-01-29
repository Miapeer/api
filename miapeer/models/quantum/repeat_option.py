from typing import Optional

from sqlmodel import Field, SQLModel


class RepeatOptionBase(SQLModel):
    name: str
    repeat_unit_id: int = Field(foreign_key="quantum_repeat_unit.repeat_unit_id")
    quantity: int
    order_index: int


class RepeatOption(RepeatOptionBase, table=True):
    __tablename__: str = "quantum_repeat_option"  # type: ignore

    repeat_option_id: Optional[int] = Field(default=None, primary_key=True)


class RepeatOptionCreate(RepeatOptionBase):
    ...


class RepeatOptionRead(RepeatOptionBase):
    repeat_option_id: int


class RepeatOptionUpdate(SQLModel):
    ...
