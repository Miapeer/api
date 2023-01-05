from typing import Optional

from sqlmodel import Field, SQLModel


class SettingBase(SQLModel):
    name: str

class Setting(SettingBase, table=True):
    setting_id: Optional[int] = Field(default=None, primary_key=True)


class SettingCreate(SettingBase):
    ...


class SettingRead(SettingBase):
    setting_id: int


class SettingUpdate(SQLModel):
    ...
