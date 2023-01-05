from typing import Optional

from sqlmodel import Field, SQLModel


class PortfolioUserSettingBase(SQLModel):
    portfolio_user_id: int = Field(foreign_key="portfolio_user.portfolio_user_id")
    setting_id: int = Field(foreign_key="setting.setting_id")
    value: str


class PortfolioUserSetting(PortfolioUserSettingBase, table=True):
    portfolio_user_setting_id: Optional[int] = Field(default=None, primary_key=True)


class PortfolioUserSettingCreate(PortfolioUserSettingBase):
    ...


class PortfolioUserSettingRead(PortfolioUserSettingBase):
    portfolio_user_setting_id: int


class PortfolioUserSettingUpdate(SQLModel):
    ...
