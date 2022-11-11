import sys

from dotenv import find_dotenv, load_dotenv

from miapeer.adapter.database import create_db_and_tables
from miapeer.app import app


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


if __name__ == "__main__":
    pass
