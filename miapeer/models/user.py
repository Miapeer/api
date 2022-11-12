from typing import Optional

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    email: str


class User(UserBase, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)


class UserCreate(UserBase):
    ...


class UserRead(UserBase):
    user_id: int


class UserUpdate(SQLModel):
    email: Optional[str] = None
