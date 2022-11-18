from os import environ as env

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from miapeer.auth import auth0, fastapi
from miapeer.routers import miapeer, miapeer_api

app = FastAPI()


app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))

app.mount("/static", StaticFiles(directory="./miapeer/static"), name="static")

app.include_router(fastapi.router)
app.include_router(miapeer.router)
app.include_router(miapeer_api.application.router)
app.include_router(miapeer_api.role.router)
app.include_router(miapeer_api.application_role.router)
app.include_router(miapeer_api.user.router)
app.include_router(miapeer_api.permission.router)
