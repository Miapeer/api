from sqlalchemy import Column, String
from sqlalchemy.dialects.mssql import BIT, UNIQUEIDENTIFIER

from database import Base


class Applications(Base):
    __tablename__ = "Applications"

    id = Column(UNIQUEIDENTIFIER, primary_key=True)
    name = Column(String)
    url = Column(String)
    description = Column(String)
    icon = Column(String)
    display = Column(BIT)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "icon": self.icon,
            "display": self.display,
            # "created_at": str(self.created_at.strftime('%d-%m-%Y'))
        }
