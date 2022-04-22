import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import jsonify, redirect, render_template, request, session, url_for

from auth import AuthError, requires_auth


def init_routes(app, oauth, schema):
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
        session["user"] = token

        token_permissions = token.get("permissions")

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

    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        response = jsonify(ex.error)
        response.status_code = ex.status_code
        return response

    @app.route("/graphql", methods=["GET"])
    def graphql_playground():
        return PLAYGROUND_HTML, 200

    @app.route("/graphql", methods=["POST"])
    @requires_auth
    def graphql_server():
        data = request.get_json()

        success, result = graphql_sync(
            schema, data, context_value=request, debug=app.debug
        )
        status_code = 200 if success else 400

        return jsonify(result), status_code
