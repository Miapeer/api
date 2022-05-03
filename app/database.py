from os import environ as env
from urllib.parse import quote_plus

from sqlmodel import SQLModel, create_engine


def connection_string():
    server = env.get("MIAPEER_DB_SERVER")
    database = env.get("MIAPEER_DB_NAME")
    username = env.get("MIAPEER_DB_USERNAME")
    password = env.get("MIAPEER_DB_PASSWORD")
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"

    return connection_string


def db_uri():
    db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string())}"
    return db_uri


engine = create_engine(db_uri(), echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# def get_all_applications():
#     with get_db(SqlAzureRepository) as db:
#         apps = db.execute(
#             "select id, name, url, description, icon, display from Applications"
#         )
#         applications = [Application(**dict(application)) for application in apps]
#     return applications


# from sqlalchemy.orm import Session

# from . import models, schemas


# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item
