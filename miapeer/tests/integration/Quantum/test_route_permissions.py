from dataclasses import dataclass

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


@dataclass
class ParamTestCase:
    method: str
    route: str
    allow_all: bool = False  # Allows "unauthorized" test to skip
    miapeer_user: bool = False
    miapeer_admin: bool = False
    miapeer_super_user: bool = False
    quantum_user: bool = False
    quantum_admin: bool = False
    quantum_super_user: bool = False


# fmt: off
authorized_tests = [
    # Give ONLY the permissions that are allowed (one at a time if multiple).

    # Root
    ParamTestCase(method="GET", route="/"),

    # Miapeer: Auth
    ParamTestCase(method="POST", route="/miapeer/v1/auth/token"),

    # Miapeer: Applications
    ParamTestCase(method="GET", route="/miapeer/v1/applications"),
    ParamTestCase(method="POST", route="/miapeer/v1/applications", miapeer_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/applications/{application_id}"),
    ParamTestCase(method="DELETE", route="/miapeer/v1/applications/{application_id}", miapeer_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/applications/{application_id}", miapeer_super_user=True),

    # Miapeer: Roles
    ParamTestCase(method="GET", route="/miapeer/v1/roles", miapeer_admin=True),
    ParamTestCase(method="POST", route="/miapeer/v1/roles", miapeer_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/roles/{role_id}", miapeer_admin=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/roles/{role_id}", miapeer_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/roles/{role_id}", miapeer_super_user=True),

    # Miapeer: ApplicationRoles
    ParamTestCase(method="GET", route="/miapeer/v1/application-roles", miapeer_super_user=True),
    ParamTestCase(method="POST", route="/miapeer/v1/application-roles", miapeer_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_super_user=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_super_user=True),

    # Miapeer: Users
    ParamTestCase(method="GET", route="/miapeer/v1/users/me"),
    ParamTestCase(method="GET", route="/miapeer/v1/users", miapeer_admin=True),
    ParamTestCase(method="POST", route="/miapeer/v1/users", miapeer_admin=True),
    ParamTestCase(method="GET", route="/miapeer/v1/users/{user_id}", miapeer_admin=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/users/{user_id}", miapeer_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/users/{user_id}", miapeer_super_user=True),

    # Miapeer: Permissions
    ParamTestCase(method="GET", route="/miapeer/v1/permissions", miapeer_admin=True),
    ParamTestCase(method="POST", route="/miapeer/v1/permissions", miapeer_admin=True),
    ParamTestCase(method="GET", route="/miapeer/v1/permissions/{permission_id}", miapeer_admin=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/permissions/{permission_id}", miapeer_admin=True),

    # Quantum: Portfolios
    ParamTestCase(method="GET", route="/quantum/v1/portfolios", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/portfolios", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/portfolios/{portfolio_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/portfolios/{portfolio_id}", quantum_super_user=True),

    # Quantum: Accounts
    ParamTestCase(method="GET", route="/quantum/v1/accounts", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}", quantum_user=True),

    # Quantum: Payees
    ParamTestCase(method="GET", route="/quantum/v1/payees", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/payees", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/payees/{payee_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/payees/{payee_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/payees/{payee_id}", quantum_user=True),

    # Quantum: TransactionTypes
    ParamTestCase(method="GET", route="/quantum/v1/transaction-types", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/transaction-types", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/transaction-types/{transaction_type_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/transaction-types/{transaction_type_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/transaction-types/{transaction_type_id}", quantum_user=True),

    # Quantum: Categories
    ParamTestCase(method="GET", route="/quantum/v1/categories", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/categories", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/categories/{category_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/categories/{category_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/categories/{category_id}", quantum_user=True),

    # Quantum: Transactions
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/transactions", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/transactions", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", quantum_user=True),

    # Quantum: ScheduledTransactions
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/scheduled-transactions", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions", quantum_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", quantum_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", quantum_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}/create-transaction", quantum_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}/skip-iteration", quantum_user=True),

    # Quantum: RepeatOptions
    ParamTestCase(method="GET", route="/quantum/v1/repeat-options", quantum_user=True),
]

unauthorized_tests = [
    # Give ALL the permissions, EXCEPT the ones that are actually allowed

    # Root
    ParamTestCase(method="GET", route="/", allow_all=True),

    # Miapeer: Auth
    ParamTestCase(method="POST", route="/miapeer/v1/auth/token", allow_all=True),

    # Miapeer: Applications
    ParamTestCase(method="GET", route="/miapeer/v1/applications", allow_all=True),
    ParamTestCase(method="POST", route="/miapeer/v1/applications", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/applications/{application_id}", allow_all=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/applications/{application_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/applications/{application_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),

    # Miapeer: Roles
    ParamTestCase(method="GET", route="/miapeer/v1/roles", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/miapeer/v1/roles", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/roles/{role_id}", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/roles/{role_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/roles/{role_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),

    # Miapeer: ApplicationRoles
    ParamTestCase(method="GET", route="/miapeer/v1/application-roles", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/miapeer/v1/application-roles", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/application-roles/{application_role_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),

    # Miapeer: Users
    ParamTestCase(method="GET", route="/miapeer/v1/users/me", allow_all=True),
    ParamTestCase(method="GET", route="/miapeer/v1/users", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/miapeer/v1/users", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/users/{user_id}", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/users/{user_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/miapeer/v1/users/{user_id}", miapeer_user=True, miapeer_admin=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),

    # Miapeer: Permissions
    ParamTestCase(method="GET", route="/miapeer/v1/permissions", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/miapeer/v1/permissions", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/miapeer/v1/permissions/{permission_id}", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/miapeer/v1/permissions/{permission_id}", miapeer_user=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: Portfolios
    ParamTestCase(method="GET", route="/quantum/v1/portfolios", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/portfolios", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/portfolios/{portfolio_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/portfolios/{portfolio_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_user=True, quantum_admin=True),

    # Quantum: Accounts
    ParamTestCase(method="GET", route="/quantum/v1/accounts", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: Payees
    ParamTestCase(method="GET", route="/quantum/v1/payees", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/payees", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/payees/{payee_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/payees/{payee_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/payees/{payee_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: TransactionTypes
    ParamTestCase(method="GET", route="/quantum/v1/transaction-types", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/transaction-types", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/transaction-types/{transaction_type_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/transaction-types/{transaction_type_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/transaction-types/{transaction_type_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: Categories
    ParamTestCase(method="GET", route="/quantum/v1/categories", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/categories", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/categories/{category_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/categories/{category_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/categories/{category_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: Transactions
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/transactions", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/transactions", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}/transactions/{transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: ScheduledTransactions
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/scheduled-transactions", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="GET", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="DELETE", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="PATCH", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}/create-transaction", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
    ParamTestCase(method="POST", route="/quantum/v1/accounts/{account_id}/scheduled-transactions/{scheduled_transaction_id}/skip-iteration", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),

    # Quantum: RepeatOptions
    ParamTestCase(method="GET", route="/quantum/v1/repeat-options", miapeer_user=True, miapeer_admin=True, miapeer_super_user=True, quantum_admin=True, quantum_super_user=True),
]
# fmt: on


class TestPermissions:
    def test_check_for_untested_routes(self, client: TestClient) -> None:
        # Make sure all request routes/methods are accounted for in both the "authorized" and "unauthorized" test sets.
        #   This test will fail if a route is missing (e.g. a new route was added)

        for route in client.app.routes:  # type: ignore
            if isinstance(route, APIRoute):
                for method in route.methods:
                    print(f"Testing {method}: {route.path}")

                    # Exists in "authorized" test set
                    print("  authorized")
                    assert [
                        t for t in authorized_tests if t.route == route.path and t.method == method
                    ], f'"Authorized" test missing for route "{route.path}"'
                    print("    success")

                    # Exists in "unauthorized" test set
                    print("  unauthorized")
                    assert [
                        t for t in unauthorized_tests if t.route == route.path and t.method == method
                    ], f'"Unauthorized" test missing for route "{route.path}"'
                    print("    success")

    @pytest.mark.parametrize(
        "method, route, miapeer_user, miapeer_admin, miapeer_super_user, quantum_user, quantum_admin, quantum_super_user",
        [
            (
                t.method,
                t.route,
                t.miapeer_user,
                t.miapeer_admin,
                t.miapeer_super_user,
                t.quantum_user,
                t.quantum_admin,
                t.quantum_super_user,
            )
            for t in authorized_tests
        ],
    )
    def test_permissions_authorized(self, client: TestClient, method: str, route: str) -> None:
        client_method = getattr(client, method.lower())
        response = client_method(route)

        # Anything other than 400 should be good to go, but we'll capture specific ones for now.
        #   More than likely, other error-based exceptions will be thrown due to the lack of body, data, etc.
        assert response.is_server_error is False

        allowed_responses = [
            (200, "OK"),
            (404, "Not Found"),
            (422, "Unprocessable Entity"),
        ]

        assert (response.status_code, response.reason_phrase) in allowed_responses

    @pytest.mark.parametrize(
        "method, route, allow_anonymous, miapeer_user, miapeer_admin, miapeer_super_user, quantum_user, quantum_admin, quantum_super_user",
        [
            (
                t.method,
                t.route,
                t.allow_all,
                t.miapeer_user,
                t.miapeer_admin,
                t.miapeer_super_user,
                t.quantum_user,
                t.quantum_admin,
                t.quantum_super_user,
            )
            for t in unauthorized_tests
        ],
    )
    def test_permissions_not_authorized(self, client: TestClient, method: str, route: str, allow_anonymous: bool) -> None:
        if allow_anonymous:
            # We can just skip this test since no request is unauthorized
            return

        client_method = getattr(client, method.lower())
        response = client_method(route)

        # The request should fail specifically for lack of permission above all else
        assert response.status_code == 400
        assert response.text == '{"detail":"Unauthorized"}'
