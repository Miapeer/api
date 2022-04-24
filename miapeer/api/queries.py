import typing

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.permission import BasePermission
from strawberry.types import Info

from auth import requires_auth, requires_scope


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    async def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return requires_auth(info.context["request"])


class IsTest(BasePermission):
    message = "User is not TEST"

    async def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return requires_scope(info.context["request"], "zzz")


class IsZomething(BasePermission):
    message = "User is not Zomething"

    async def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return requires_scope(info.context["request"], "write:zomething")


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

    @strawberry.field(permission_classes=[IsAuthenticated, IsZomething])
    def hello_p(self) -> str:
        return "PROTECTED: Hello World"


schema = strawberry.Schema(Query)


graphql_app = GraphQLRouter(schema)


# app = FastAPI()
# app.include_router(graphql_app, prefix="/graphql")
