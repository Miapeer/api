from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

# from miapeer.models.permission import Permission


class ApplicationBase(SQLModel):
    name: str
    url: str
    description: str
    icon: str
    display: bool
    # permission_id: Optional[int] = Field(default=None, primary_key=True)


class Application(ApplicationBase, table=True):
    application_id: Optional[int] = Field(default=None, primary_key=True)
    # permissions: list[Permission] = Relationship(back_populates="application")
    ...


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


# class HeroReadWithTeam(HeroRead):
#     team: Optional[TeamRead] = None


# class TeamReadWithHeroes(TeamRead):
#     heroes: List[HeroRead] = []


# class Hero(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     secret_name: str
#     age: Optional[int] = None


#     items = relationship("Item", back_populates="owner")


# class Item(Base):
#     __tablename__ = "items"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String, index=True)
#     owner_id = Column(Integer, ForeignKey("users.id"))

#     owner = relationship("User", back_populates="items")


# from typing import List, Optional

# from sqlmodel import Field, Relationship, SQLModel


# class Team(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     headquarters: str

#     heroes: List["Hero"] = Relationship(back_populates="team")


# class Hero(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     secret_name: str
#     age: Optional[int] = Field(default=None, index=True)

#     team_id: Optional[int] = Field(default=None, foreign_key="team.id")
#     team: Optional[Team] = Relationship(back_populates="heroes")
