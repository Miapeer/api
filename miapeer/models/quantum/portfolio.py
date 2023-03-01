from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioBase(SQLModel):
    ...


class Portfolio(PortfolioBase, table=True):
    __tablename__: str = "quantum_portfolio"  # type: ignore

    portfolio_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio_users: List["PortfolioUser"] = Relationship(back_populates="portfolio")

    # accounts: List["Account"] = Relationship(back_populates="portfolio")
    # transaction_types: List["TransactionType"] = Relationship(back_populates="portfolio")
    # payees: List["Payee"] = Relationship(back_populates="portfolio")
    # categories: List["Category"] = Relationship(back_populates="portfolio")


class PortfolioCreate(PortfolioBase):
    ...


class PortfolioRead(PortfolioBase):
    portfolio_id: int


class PortfolioUpdate(SQLModel):
    ...
