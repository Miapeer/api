from os import environ as env

from ariadne import (
    QueryType,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, _app_ctx_stack
from flask_cors import CORS
from sqlalchemy.orm import scoped_session

from database import SessionLocal
from miapeer.api.queries import init_resolvers as init_miapeer_resolvers
from miapeer.routes import init_routes as init_miapeer_routes

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
CORS(app)


oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


db_session = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)

type_defs = load_schema_from_path("./miapeer/api/schema.graphql")
query = QueryType()
init_miapeer_resolvers(query)
schema = make_executable_schema(type_defs, query, snake_case_fallback_resolvers)

init_miapeer_routes(app, oauth, schema)


if __name__ == "__main__":
    port = int(env.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
