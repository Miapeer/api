from sqlalchemy.dialects.mssql import BIT, UNIQUEIDENTIFIER

from app import db


class Applications(db.Model):
    __tablename__ = "Applications"

    id = db.Column(UNIQUEIDENTIFIER, primary_key=True)
    name = db.Column(db.String)
    url = db.Column(db.String)
    description = db.Column(db.String)
    icon = db.Column(db.String)
    display = db.Column(BIT)

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
