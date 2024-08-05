from os import environ as env

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from miapeer.routers import auth, miapeer, quantum

app = FastAPI()

if env.get("APP_SECRET_KEY") is None or env.get("JWT_SECRET_KEY") is None:
    raise LookupError("Secrets not found")

app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(
    tags=["Miapeer API"],
)


@router.get("/")
async def get_last_publish_date() -> HTMLResponse:
    update_str = None
    try:
        with open("last_update", "r") as f:
            update_str = f.readline()
    except Exception:
        pass

    return HTMLResponse(f"Last updated: {update_str}")


app.include_router(router)
app.include_router(auth.router)
app.include_router(miapeer.router)
app.include_router(quantum.router)
