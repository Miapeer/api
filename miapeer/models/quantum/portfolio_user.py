from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioUserBase(SQLModel):
    portfolio_id: int = Field(foreign_key="portfolio.portfolio_id")
    user_id: int = Field(foreign_key="user.user_id")

class PortfolioUser(PortfolioUserBase, table=True):
    __tablename__: str = "portfolio_user"  # type: ignore

    portfolio_user_id: Optional[int] = Field(default=None, primary_key=True)


class PortfolioUserCreate(PortfolioUserBase):
    ...


class PortfolioUserRead(PortfolioUserBase):
    portfolio_user_id: int


class PortfolioUserUpdate(SQLModel):
    ...
