from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioUserSettingBase(SQLModel):
    portfolio_user_id: int = Field(foreign_key="quantum_portfolio_user.portfolio_user_id")
    setting_id: int = Field(foreign_key="quantum_setting.setting_id")
    value: str


class PortfolioUserSetting(PortfolioUserSettingBase, table=True):
    __tablename__: str = "quantum_portfolio_user_setting"  # type: ignore

    portfolio_user_setting_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio_user: PortfolioUser = Relationship(back_populates="portfolio_user_settings")
    # setting: Setting = Relationship(back_populates="portfolio_user_settings")


class PortfolioUserSettingCreate(PortfolioUserSettingBase):
    ...


class PortfolioUserSettingRead(PortfolioUserSettingBase):
    portfolio_user_setting_id: int


class PortfolioUserSettingUpdate(SQLModel):
    ...
