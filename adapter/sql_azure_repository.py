from os import environ as env
from urllib.parse import quote_plus

from flask import _app_ctx_stack
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from adapter.miapeer_repository import MiapeerRepository
from miapeer.domain.application import Application


class SqlAzureRepository(MiapeerRepository):
    session = None
    Base = declarative_base()

    def __init__(self):
        server = env.get("MIAPEER_DB_SERVER")
        database = env.get("MIAPEER_DB_NAME")
        username = env.get("MIAPEER_DB_USERNAME")
        password = env.get("MIAPEER_DB_PASSWORD")
        driver = "{ODBC Driver 17 for SQL Server}"

        connection_string = f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
        db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"
        engine = create_engine(db_uri, connect_args={"check_same_thread": False})

        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        self.session = scoped_session(
            session_local, scopefunc=_app_ctx_stack.__ident_func__
        )

    def get_all_applications(self):
        apps = self.session.execute(
            "select id, name, url, description, icon, display from Applications"
        )
        applications = [Application(**dict(application)) for application in apps]
        return applications
