import json
from os import environ as env

from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from rich import print
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

import auth
from miapeer.api.queries import graphql_app

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))
app.include_router(auth.router)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    access_token = json.loads(request.cookies.get("user", "{}"))

    return f"""
<html>
  <head>
    <meta charset="utf-8" />
    <title>Auth0 Example</title>
  </head>
  <body>
    <h1>Welcome {access_token.get('userinfo').get('email') if access_token else 'Guest'}</h1>
    <p>{'<a href="/logout">Logout</a>' if access_token else '<a href="/login">Login</a>'}</p>
    <p>{access_token}</p>
  </body>
</html>
    """


# @app.exception_handler(AuthError)
# async def handle_auth_error(ex):
#     # response = jsonify(ex.error)
#     # response.status_code = ex.status_code
#     # return response
#     return 'error'

# @app.get("/api/public")
# def public():
#     """No access token required to access this route"""

#     result = {
#         "status": "success",
#         "msg": ("Hello from a public endpoint! You don't need to be "
#                 "authenticated to see this.")
#     }
#     return result


# @app.get("/api/private")
# def private(response: Response, token: str = Depends(token_auth_scheme)):
#     """A valid access token is required to access this route"""

#     result = VerifyToken(token.credentials).verify()

#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result

#     return result
