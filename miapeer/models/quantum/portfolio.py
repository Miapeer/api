from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioBase(SQLModel):
    ...


class Portfolio(PortfolioBase, table=True):
    __tablename__: str = "quantum_portfolio"  # type: ignore

    portfolio_id: Optional[int] = Field(default=None, primary_key=True)


class PortfolioCreate(PortfolioBase):
    ...


class PortfolioRead(PortfolioBase):
    portfolio_id: int


class PortfolioUpdate(SQLModel):
    ...
