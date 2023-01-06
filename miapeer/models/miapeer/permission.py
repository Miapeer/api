from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, MetaData


class PermissionBase(SQLModel):
    user_id: int = Field(foreign_key="miapeer_user.user_id")
    application_role_id: int = Field(foreign_key="miapeer_application_role.application_role_id")


class Permission(PermissionBase, table=True):
    __tablename__: str = "miapeer_permission"

    permission_id: Optional[int] = Field(default=None, primary_key=True)


class PermissionCreate(PermissionBase):
    ...


class PermissionRead(PermissionBase):
    permission_id: int


class PermissionUpdate(SQLModel):
    ...
