from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from miapeer.models.miapeer.permission import Permission


class UserBase(SQLModel):
    email: str


class User(UserBase, table=True):
    __tablename__: str = "miapeer_user"  # type: ignore

    user_id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    disabled: bool

    permissions: List["Permission"] = Relationship(back_populates="user")
    # portfolio_users: List["PortfolioUser"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    ...


class UserRead(UserBase):
    user_id: int


class UserUpdate(SQLModel):
    email: Optional[str] = None
