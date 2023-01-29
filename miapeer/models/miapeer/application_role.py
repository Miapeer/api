from typing import Optional

from sqlmodel import Field, SQLModel

# if TYPE_CHECKING:
#     from miapeer.models.miapeer.application import ApplicationRead


class ApplicationRoleBase(SQLModel):
    application_id: int = Field(schema_extra={"schema": "miapeer"}, foreign_key="miapeer_application.application_id")
    role_id: int = Field(foreign_key="miapeer_role.role_id")
    description: str = Field(default=None)


class ApplicationRole(ApplicationRoleBase, table=True):
    __tablename__: str = "miapeer_application_role"  # type: ignore

    application_role_id: Optional[int] = Field(default=None, primary_key=True)


class ApplicationRoleCreate(ApplicationRoleBase):
    ...


class ApplicationRoleRead(ApplicationRoleBase):
    application_role_id: int
    # application: Optional["ApplicationRead"] = Relationship(back_populates="application_roles")


class ApplicationRoleUpdate(SQLModel):
    ...
