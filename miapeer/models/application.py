from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class ApplicationBase(SQLModel):
    name: str
    url: str
    description: str
    icon: str
    display: bool


class Application(ApplicationBase, table=True):
    application_id: Optional[int] = Field(default=None, primary_key=True)


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    application_id: int


class ApplicationUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display: Optional[bool] = None
