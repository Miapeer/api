from typing import Optional

from sqlmodel import Field, SQLModel

# if TYPE_CHECKING:
#     from miapeer.models.miapeer.application_role import ApplicationRoleRead


class ApplicationBase(SQLModel):
    name: str
    url: str
    description: str
    icon: str
    display: bool


class Application(ApplicationBase, table=True):
    __tablename__: str = "miapeer_application"  # type: ignore

    application_id: Optional[int] = Field(default=None, primary_key=True)


class ApplicationCreate(ApplicationBase):
    ...


class ApplicationRead(ApplicationBase):
    application_id: int
    # application_roles: list["ApplicationRoleRead"] = Relationship(back_populates="application")


class ApplicationUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display: Optional[bool] = None
