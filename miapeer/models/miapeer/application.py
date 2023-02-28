from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from miapeer.models.miapeer.application_role import ApplicationRole


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
