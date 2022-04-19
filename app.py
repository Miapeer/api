import os

from ariadne import (
    QueryType,
    graphql_sync,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from ariadne.constants import PLAYGROUND_HTML
from flask import _request_ctx_stack, jsonify, request

from auth import AuthError, requires_auth
from miapeer.api import app, db
from miapeer.api.queries import getApplications_resolver

query = QueryType()


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


type_defs = load_schema_from_path("./miapeer/api/schema.graphql")
query.set_field("getApplications", getApplications_resolver)
schema = make_executable_schema(type_defs, query, snake_case_fallback_resolvers)


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@app.route("/graphql", methods=["POST"])
@requires_auth
def graphql_server():
    data = request.get_json()

    print(f"graphql_server: {data}")

    success, result = graphql_sync(schema, data, context_value=request, debug=app.debug)
    status_code = 200 if success else 400

    return jsonify(result), status_code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
