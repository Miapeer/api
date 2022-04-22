from functools import partial

from ariadne import (
    ObjectType,
    graphql_sync,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from rich import print

import app
from adapter.miapeer_repository import MiapeerRepository
from auth import requires_scope


def init_resolvers(query, repository: MiapeerRepository):
    query.set_field(
        "getApplications", partial(applications_resolver, repository=repository)
    )


def applications_resolver(obj, info, repository: MiapeerRepository):
    try:
        apps = repository.get_all_applications()

        payload = {"success": True, "applications": apps}
    except Exception as error:
        print(error)
        payload = {"success": False, "errors": [str(error)]}
    return payload
