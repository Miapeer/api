from typing import Optional

from sqlmodel import Field, SQLModel


class RepeatUnitBase(SQLModel):
    name: str

class RepeatUnit(RepeatUnitBase, table=True):
    repeat_unit_id: Optional[int] = Field(default=None, primary_key=True)


class RepeatUnitCreate(RepeatUnitBase):
    ...


class RepeatUnitRead(RepeatUnitBase):
    repeat_unit_id: int


class RepeatUnitUpdate(SQLModel):
    ...