from os import environ as env

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from rich import print
from starlette.middleware.sessions import SessionMiddleware

from app.api.queries import graphql_app
from app.auth import auth0
from app.database import create_db_and_tables
from app.routers import miapeer, miapeer_api

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))
app.include_router(auth0.router)
app.include_router(miapeer.router)
app.include_router(miapeer_api.router)
app.include_router(graphql_app, prefix="/graphql")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# @app.exception_handler(AuthError)
# async def handle_auth_error(ex):
#     # response = jsonify(ex.error)
#     # response.status_code = ex.status_code
#     # return response
#     return 'error'

# @app.get("/api/public")
# def public():
#     """No access token required to access this route"""

#     result = {
#         "status": "success",
#         "msg": ("Hello from a public endpoint! You don't need to be "
#                 "authenticated to see this.")
#     }
#     return result
