from os import environ as env

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from miapeer.routers import auth, miapeer, miapeer_api

app = FastAPI()

if env.get("APP_SECRET_KEY") is None or env.get("JWT_SECRET_KEY") is None:
    raise LookupError("Secrets not found")

app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))

app.mount("/static", StaticFiles(directory="./miapeer/static"), name="static")

app.include_router(auth.router)
app.include_router(miapeer.router)
app.include_router(miapeer_api.router)
