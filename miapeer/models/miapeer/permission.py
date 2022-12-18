from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class PermissionBase(SQLModel):
    user_id: int = Field(foreign_key="user.user_id")
    application_role_id: int = Field(foreign_key="application_role.application_role_id")


class Permission(PermissionBase, table=True):
    permission_id: Optional[int] = Field(default=None, primary_key=True)


class PermissionCreate(PermissionBase):
    ...


class PermissionRead(PermissionBase):
    permission_id: int


class PermissionUpdate(SQLModel):
    ...
