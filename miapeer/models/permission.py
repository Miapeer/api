from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class PermissionBase(SQLModel):
    application_id: int = Field(foreign_key="application.application_id")
    user_id: int = Field(foreign_key="user.user_id")
    role_id: int = Field(foreign_key="role.role_id")


class Permission(PermissionBase, table=True):
    permission_id: Optional[int] = Field(default=None, primary_key=True)


class PermissionCreate(PermissionBase):
    pass


class PermissionRead(PermissionBase):
    permission_id: int


class PermissionUpdate(SQLModel):
    ...
