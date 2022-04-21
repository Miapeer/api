# from os import environ as env
# from urllib.parse import quote_plus

# from flask_sqlalchemy import SQLAlchemy
# from miapeer_repository import MiapeerRepository

# from app import MiapeerApp

# app = MiapeerApp()


# class SqlAzureRepository(MiapeerRepository):
#     db = None

#     def __init__(self, app):
#         server = env.get("MIAPEER_DB_SERVER")
#         database = env.get("MIAPEER_DB_NAME")
#         username = env.get("MIAPEER_DB_USERNAME")
#         password = env.get("MIAPEER_DB_PASSWORD")
#         driver = "{ODBC Driver 17 for SQL Server}"

#         connection_string = f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
#         db_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"

#         app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
#         app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#         self.db = SQLAlchemy(app)
