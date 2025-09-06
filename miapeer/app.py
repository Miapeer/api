
from os import environ as env
from dotenv import load_dotenv


from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from miapeer.routers import auth, miapeer, quantum

load_dotenv()
app = FastAPI()

app_secret_key = env.get("APP_SECRET_KEY")
jwt_secret_key = env.get("JWT_SECRET_KEY")

if not app_secret_key or not jwt_secret_key:
    raise LookupError("Secrets not found")

app.add_middleware(SessionMiddleware, secret_key=app_secret_key)

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
