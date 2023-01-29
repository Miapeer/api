from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioUserBase(SQLModel):
    portfolio_id: int = Field(foreign_key="quantum_portfolio.portfolio_id")
    user_id: int = Field(foreign_key="miapeer_user.user_id")


class PortfolioUser(PortfolioUserBase, table=True):
    __tablename__: str = "quantum_portfolio_user"  # type: ignore

    portfolio_user_id: Optional[int] = Field(default=None, primary_key=True)


class PortfolioUserCreate(PortfolioUserBase):
    ...


class PortfolioUserRead(PortfolioUserBase):
    portfolio_user_id: int


class PortfolioUserUpdate(SQLModel):
    ...
