from os import environ as env
from urllib.parse import quote_plus
from venv import create

from requests import session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

server = env.get("MIAPEER_DB_SERVER")
database = env.get("MIAPEER_DB_NAME")
username = env.get("MIAPEER_DB_USERNAME")
password = env.get("MIAPEER_DB_PASSWORD")
driver = "{ODBC Driver 17 for SQL Server}"

connection_string = f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"
engine = create_engine(db_uri, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
