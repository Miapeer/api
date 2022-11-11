import sys

print(sys.path)
from dotenv import find_dotenv, load_dotenv

from miapeer.adapter.database import create_db_and_tables

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

from miapeer.app import app


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


if __name__ == "__main__":
    pass
