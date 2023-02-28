from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from miapeer.models.miapeer.application_role import ApplicationRole


class RoleBase(SQLModel):
    name: str


class Role(RoleBase, table=True):
    __tablename__: str = "miapeer_role"  # type: ignore

    role_id: Optional[int] = Field(default=None, primary_key=True)

    application_roles: List["ApplicationRole"] = Relationship(back_populates="role")


class RoleCreate(RoleBase):
    ...


class RoleRead(RoleBase):
    role_id: int


class RoleUpdate(SQLModel):
    name: Optional[str] = None
