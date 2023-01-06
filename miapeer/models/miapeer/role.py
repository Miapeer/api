from typing import Optional

from sqlmodel import Field, SQLModel


class RoleBase(SQLModel):
    name: str


class Role(RoleBase, table=True):
    __tablename__: str = "miapeer_role"  # type: ignore

    role_id: Optional[int] = Field(default=None, primary_key=True)


class RoleCreate(RoleBase):
    ...


class RoleRead(RoleBase):
    role_id: int


class RoleUpdate(SQLModel):
    name: Optional[str] = None
