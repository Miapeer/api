from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class ApplicationRoleBase(SQLModel):
    application_id: int = Field(foreign_key="application.application_id")
    role_id: int = Field(foreign_key="role.role_id")


class ApplicationRole(ApplicationRoleBase, table=True):
    __tablename__: str = "application_role"  # type: ignore

    application_role_id: Optional[int] = Field(default=None, primary_key=True)


class ApplicationRoleCreate(ApplicationRoleBase):
    ...


class ApplicationRoleRead(ApplicationRoleBase):
    application_role_id: int


class ApplicationRoleUpdate(SQLModel):
    ...
