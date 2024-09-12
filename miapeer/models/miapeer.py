from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

# region: Auth


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# endregion


# region: User


class UserBase(SQLModel):
    email: str
    disabled: bool


class User(UserBase, table=True):
    __tablename__: str = "miapeer_user"  # type: ignore

    user_id: Optional[int] = Field(default=None, primary_key=True)
    password: str

    permissions: List["Permission"] = Relationship(back_populates="user")
    # portfolio_users: List["PortfolioUser"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    user_id: int


class UserUpdate(SQLModel):
    email: Optional[str] = None
    password: Optional[str] = None


# endregion


# region: Application


class ApplicationBase(SQLModel):
    name: str
    url: str
    description: str
    icon: str
    display: bool


class Application(ApplicationBase, table=True):
    __tablename__: str = "miapeer_application"  # type: ignore

    application_id: Optional[int] = Field(default=None, primary_key=True)
    application_roles: List["ApplicationRole"] = Relationship(back_populates="application")


class ApplicationCreate(ApplicationBase):
    ...


class ApplicationRead(ApplicationBase):
    application_id: int


class ApplicationUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display: Optional[bool] = None


# endregion


# region: Role


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


# endregion


# region: Application-Role


class ApplicationRoleBase(SQLModel):
    application_id: int = Field(schema_extra={"schema": "miapeer"}, foreign_key="miapeer_application.application_id")
    role_id: int = Field(foreign_key="miapeer_role.role_id")
    description: str = Field(default=None)
    UniqueConstraint("application_id", "role_id", name="UIX_application_role")


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

    # application: Application
    # role: Role


class ApplicationRoleUpdate(SQLModel):
    description: Optional[str]


# ApplicationRoleRead.model_rebuild()

# endregion


# region: Permission


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

    # user: User
    # application_role: ApplicationRoleRead


class PermissionUpdate(SQLModel):
    ...


# endregion


# region Finalization steps

ApplicationRoleRead.model_rebuild()

# endregion
