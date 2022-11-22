from os import environ as env
from urllib.parse import quote_plus

from sqlalchemy.engine.base import Engine
from sqlmodel import SQLModel, create_engine


def connection_string() -> str:
    server = env.get("MIAPEER_DB_SERVER")
    database = env.get("MIAPEER_DB_NAME")
    username = env.get("MIAPEER_DB_USERNAME")
    password = env.get("MIAPEER_DB_PASSWORD")
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = (
        f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
    )

    return connection_string


def db_uri() -> str:
    db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string())}"
    return db_uri


connect_args = {"check_same_thread": False}
engine: Engine = create_engine(db_uri(), echo=True, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
