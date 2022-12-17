from os import environ as env

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from miapeer.routers import auth, miapeer, miapeer_api

app = FastAPI()

if env.get("APP_SECRET_KEY") is None or env.get("JWT_SECRET_KEY") is None:
    raise LookupError("Secrets not found")

app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))

origins = [
    "http://www.miapeer.com",
    "https://www.miapeer.com",
    "http://miapeer.azurewebsites.net",
    "https://miapeer.azurewebsites.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="./miapeer/static"), name="static")

app.include_router(auth.router)
app.include_router(miapeer.router)
app.include_router(miapeer_api.router)
