from os import environ as env
from urllib.parse import quote_plus

from sqlalchemy.engine.base import Engine
from sqlmodel import SQLModel, create_engine
from sqlalchemy import text


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
    dev_db_uri = f"sqlite:///./miapeer.db"
    prod_db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string())}"

    return prod_db_uri if env.get("MIAPEER_ENV") == 'Production' else dev_db_uri


engine: Engine = create_engine(db_uri(), connect_args={"check_same_thread": False}, echo=True)

def get_user_count() -> int:
    with engine.connect() as connection:
        result = connection.execute(text("select count(*) from [user]")).one()
        
    return result[0]

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

    if get_user_count() == 0:
        seed_db()

def seed_db() -> None:
    print('seed_db')

    superuser_username = env.get("MIAPEER_DB_SEED_SUPERUSER_USERNAME")
    superuser_password = env.get("MIAPEER_DB_SEED_SUPERUSER_PASSWORD")

    admin_username = env.get("MIAPEER_DB_SEED_ADMIN_USERNAME")
    admin_password = env.get("MIAPEER_DB_SEED_ADMIN_PASSWORD")

    with engine.connect() as connection:
        # Applications
        connection.execute(text("insert into application (name, url, description, icon, display) values ('Miapeer', 'https://www.miapeer.com', 'Ignore this, it is just a test placeholder', 'icon icon-1 fa fa-ban', 0)"))
        connection.execute(text("insert into application (name, url, description, icon, display) values ('Quantum', 'https://quantum.miapeer.com', 'A free budgeting and money management web app.<br /><br />With its focus on forecasting, Quantum will help you be proactive rather than reactive.', 'icon icon-1 fa fa-usd', 1)"))
    
        # Roles
        connection.execute(text("insert into role (name) values ('Super User')"))
        connection.execute(text("insert into role (name) values ('Administrator')"))
        connection.execute(text("insert into role (name) values ('User')"))
    
        # ApplicationRoles
        connection.execute(text("insert into application_role (application_id, role_id) values (1, 1)"))
        connection.execute(text("insert into application_role (application_id, role_id) values (1, 2)"))
        connection.execute(text("insert into application_role (application_id, role_id) values (1, 3)"))
        connection.execute(text("insert into application_role (application_id, role_id) values (2, 1)"))
        connection.execute(text("insert into application_role (application_id, role_id) values (2, 2)"))
        connection.execute(text("insert into application_role (application_id, role_id) values (2, 3)"))
    
        # Users
        connection.execute(text(f"insert into [user] (email, password, disabled) values ('{superuser_username}', '{superuser_password}', 0)"))
        connection.execute(text(f"insert into [user] (email, password, disabled) values ('{admin_username}', '{admin_password}', 0)"))
    
        # Permissions
        connection.execute(text("insert into permission (user_id, application_role_id) values (1, 1)"))
        connection.execute(text("insert into permission (user_id, application_role_id) values (2, 3)"))
        connection.execute(text("insert into permission (user_id, application_role_id) values (2, 6)"))

        connection.commit()
