from os import environ as env
from urllib.parse import quote_plus

from sqlalchemy.engine.base import Engine
from sqlmodel import SQLModel, create_engine, Session
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
        from miapeer.models.miapeer.application import Application
        from miapeer.models.miapeer.role import Role
        from miapeer.models.miapeer.application_role import ApplicationRole
        from miapeer.models.miapeer.user import User
        from miapeer.models.miapeer.permission import Permission
        from miapeer.models.quantum.repeat_unit import RepeatUnit
        from miapeer.models.quantum.repeat_option import RepeatOption

        with Session(engine) as db:
            # Miapeer: Applications
            db.add_all([
                miapeer := Application(name='Miapeer', url='https://www.miapeer.com', description='Ignore this, it is just a test placeholder', icon='icon icon-1 fa fa-ban', display=False),
                quantum := Application(name='Quantum', url='https://quantum.miapeer.com', description='A free budgeting and money management web app.<br /><br />With its focus on forecasting, Quantum will help you be proactive rather than reactive.', icon='icon icon-1 fa fa-usd', display=True),
            ])

            db.commit()
            db.refresh(miapeer)
            db.refresh(quantum)

            # Miapeer: Roles
            db.add_all([
                super_user_role := Role(name='Super User'),
                admin_role := Role(name='Administrator'),
                user_role := Role(name='User'),
            ])

            db.commit()
            db.refresh(super_user_role)
            db.refresh(admin_role)
            db.refresh(user_role)

            # Miapeer: ApplicationRoles
            db.add_all([
                miapeer_super_user := ApplicationRole(application_id=miapeer.application_id, role_id=super_user_role.role_id, description='Can create applications'),    
                miapeer_admin := ApplicationRole(application_id=miapeer.application_id, role_id=admin_role.role_id, description='Can create users and assign users to applications'),    
                miapeer_user := ApplicationRole(application_id=miapeer.application_id, role_id=user_role.role_id, description='Can access their applications'),    
                quantum_super_user := ApplicationRole(application_id=quantum.application_id, role_id=super_user_role.role_id, description='Can add Administrators to their Portfolios'),    
                quantum_admin := ApplicationRole(application_id=quantum.application_id, role_id=admin_role.role_id, description='Can add Users to their Portfolios'),    
                quantum_user := ApplicationRole(application_id=quantum.application_id, role_id=user_role.role_id, description='Can access their associated Portfolios'),    
            ])

            db.commit()
            db.refresh(miapeer_super_user)
            db.refresh(miapeer_admin)
            db.refresh(miapeer_user)
            db.refresh(quantum_super_user)
            db.refresh(quantum_admin)
            db.refresh(quantum_user)
    
            # Miapeer: Users
            db.add_all([
                super_user := User(email=superuser_username, password=superuser_password, disabled=False),
                admin := User(email=admin_username, password=admin_password, disabled=False),
            ])

            db.commit()
            db.refresh(super_user)
            db.refresh(admin)
    
            # Miapeer: Permissions
            db.add_all([
                Permission(user_id=super_user.user_id, application_role_id=miapeer_super_user.application_role_id),
                Permission(user_id=admin.user_id, application_role_id=miapeer_user.application_role_id),
                Permission(user_id=admin.user_id, application_role_id=quantum_user.application_role_id),
            ])

            db.commit()
            
            # Quantum: Repeat Units
            db.add_all([
                day := RepeatUnit(name='Day'),
                month := RepeatUnit(name='Month'),
                year := RepeatUnit(name='Year'),
            ])

            db.commit()
            db.refresh(day)
            db.refresh(month)
            db.refresh(year)

            # Quantum: Repeat Options
            db.add_all([
                RepeatOption(name='Weekly', repeat_unit_id=day.repeat_unit_id, quantity=7, order_index=1),
                RepeatOption(name='Bi-Weekly', repeat_unit_id=day.repeat_unit_id, quantity=14, order_index=2),
                RepeatOption(name='Monthly', repeat_unit_id=month.repeat_unit_id, quantity=1, order_index=3),
                RepeatOption(name='Quarterly', repeat_unit_id=month.repeat_unit_id, quantity=3, order_index=4),
                RepeatOption(name='Semi-Anually', repeat_unit_id=month.repeat_unit_id, quantity=6, order_index=5),
                RepeatOption(name='Anually', repeat_unit_id=year.repeat_unit_id, quantity=1, order_index=6),
            ])

            db.commit()
