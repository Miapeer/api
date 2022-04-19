import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

CORS(app)

server = env.get("MIAPEER_DB_SERVER")
database = env.get("MIAPEER_DB_NAME")
username = env.get("MIAPEER_DB_USERNAME")
password = env.get("MIAPEER_DB_PASSWORD")
driver = "{ODBC Driver 17 for SQL Server}"

connection_string = f"DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}"

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


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


@app.route("/")
def home():
    # return_value = ""

    # try:
    #     rs = db.session.execute("select * from Applications")
    #     for row in rs:
    #         return_value = f"{return_value}<div>{row}</div><br/><br/><br/>"
    # except Exception:
    #     import traceback
    #     return traceback.format_exc()
    #     # return traceback.format_exception()
    #     # return "Error"

    # return return_value
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        audience="https://api.miapeer.com",
    )


@app.route("/signin-auth0")
def callback():
    token = oauth.auth0.authorize_access_token()
    print(f"{token=}")
    session["user"] = token

    token_permissions = token.get("permissions")
    print(f"{token_permissions=}")

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
