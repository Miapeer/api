from os import environ as env

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from miapeer.auth import auth0
from miapeer.routers import miapeer, miapeer_api

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))
app.include_router(auth0.router)
app.include_router(miapeer.router)
app.include_router(miapeer_api.router)
