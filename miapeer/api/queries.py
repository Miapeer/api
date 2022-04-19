from ariadne import (
    ObjectType,
    graphql_sync,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)

# from app import query
from auth import requires_scope

from .models import Applications

# query = ObjectType("Query")

# @query.field("getApplications")
def getApplications_resolver(obj, info):
    try:
        print("getApplications_resolver")
        applications = [
            application.to_dict() for application in Applications.query.all()
        ]
        print(applications)
        payload = {"success": True, "applications": applications}
    except Exception as error:
        payload = {"success": False, "errors": [str(error)]}
    return payload
