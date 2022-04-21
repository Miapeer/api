from ariadne import (
    ObjectType,
    graphql_sync,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from rich import print

import app
from auth import requires_scope

from .models import Applications


def init_resolvers(query):
    query.set_field("getApplications", getApplications_resolver)


# query = ObjectType("Query")

# @query.field("getApplications")
def getApplications_resolver(obj, info):
    print("getApplications_resolver")
    try:
        apps = app.db_session.query(Applications)
        print(apps)
        applications = [application.to_dict() for application in apps]
        print(applications)
        payload = {"success": True, "applications": applications}
    except Exception as error:
        print(error)
        payload = {"success": False, "errors": [str(error)]}
    return payload
