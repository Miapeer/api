from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from miapeer.models.miapeer.application import Application
from miapeer.models.miapeer.role import Role

if TYPE_CHECKING:
    from miapeer.models.miapeer.permission import Permission


class ApplicationRoleBase(SQLModel):
    application_id: int = Field(schema_extra={"schema": "miapeer"}, foreign_key="miapeer_application.application_id")
    role_id: int = Field(foreign_key="miapeer_role.role_id")
    description: str = Field(default=None)


class ApplicationRole(ApplicationRoleBase, table=True):
    __tablename__: str = "miapeer_application_role"  # type: ignore

    application_role_id: Optional[int] = Field(default=None, primary_key=True)

    application: Application = Relationship(back_populates="application_roles")
    role: Role = Relationship(back_populates="application_roles")

    permissions: List["Permission"] = Relationship(back_populates="application_role")


class ApplicationRoleCreate(ApplicationRoleBase):
    ...


class ApplicationRoleRead(ApplicationRoleBase):
    application_role_id: int

    application: Optional[Application] = None
    role: Optional[Role] = None


class ApplicationRoleUpdate(SQLModel):
    ...
