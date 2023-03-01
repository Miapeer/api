from typing import Optional

from sqlmodel import Field, SQLModel


class SettingBase(SQLModel):
    name: str


class Setting(SettingBase, table=True):
    __tablename__: str = "quantum_setting"  # type: ignore

    setting_id: Optional[int] = Field(default=None, primary_key=True)

    # portfolio_user_settings: List["PortfolioUserSetting"] = Relationship(back_populates="setting")


class SettingCreate(SettingBase):
    ...


class SettingRead(SettingBase):
    setting_id: int


class SettingUpdate(SQLModel):
    ...
