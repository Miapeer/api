from os import environ as env

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from miapeer.routers import auth, miapeer, quantum

app = FastAPI()

if env.get("APP_SECRET_KEY") is None or env.get("JWT_SECRET_KEY") is None:
    raise LookupError("Secrets not found")

app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))

# TODO: Update these for prod/dev? Also, Azure WebApp config helps with this.
origins = [
    "http://www.miapeer.com",
    "https://www.miapeer.com",
    "http://miapeer.azurewebsites.net",
    "https://miapeer.azurewebsites.net",
    "http://localhost:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(miapeer.router)
app.include_router(quantum.router)
