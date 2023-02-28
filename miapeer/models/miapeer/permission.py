from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from miapeer.models.miapeer.application_role import (
    ApplicationRole,
    ApplicationRoleRead,
)
from miapeer.models.miapeer.user import User


class PermissionBase(SQLModel):
    user_id: int = Field(foreign_key="miapeer_user.user_id")
    application_role_id: int = Field(foreign_key="miapeer_application_role.application_role_id")


class Permission(PermissionBase, table=True):
    __tablename__: str = "miapeer_permission"  # type: ignore

    permission_id: Optional[int] = Field(default=None, primary_key=True)

    user: User = Relationship(back_populates="permissions")
    application_role: ApplicationRole = Relationship(back_populates="permissions")


class PermissionCreate(PermissionBase):
    ...


class PermissionRead(PermissionBase):
    permission_id: int

    user: Optional[User] = None
    application_role: Optional[ApplicationRoleRead] = None


class PermissionUpdate(SQLModel):
    ...
