from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.payee import (
    Payee,
    PayeeCreate,
    PayeeRead,
    PayeeUpdate,
)
from miapeer.routers.quantum import payee

pytestmark = pytest.mark.asyncio


raw_payee_id = 12345


@pytest.fixture
def payee_id() -> int:
    return raw_payee_id


@pytest.fixture
def payee_name() -> str:
    return "transaction type name"


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_payee(payee_name: str, portfolio_id: int) -> Payee:
    return Payee(payee_id=None, name=payee_name, portfolio_id=portfolio_id)


@pytest.fixture
def complete_payee(payee_id: int, basic_payee: Payee) -> Payee:
    return Payee.model_validate(basic_payee.model_dump(), update={"payee_id": payee_id})


class TestGetAll:
    @pytest.fixture
    def multiple_payees(self, complete_payee: Payee) -> list[Payee]:
        return [complete_payee, complete_payee]

    @pytest.fixture
    def expected_multiple_payees(self, complete_payee: Payee) -> list[PayeeRead]:
        working_payee = PayeeRead.model_validate(complete_payee)
        return [working_payee, working_payee]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_payees"), lazy_fixture("expected_multiple_payees"))],
    )
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, expected_response: list[PayeeRead]) -> None:
        response = await payee.get_all_payees(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.payee_id = raw_payee_id

    @pytest.fixture
    def payee_to_create(self, payee_name: str, portfolio_id: int) -> PayeeCreate:
        return PayeeCreate(name=payee_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        payee_to_create: PayeeCreate,
        complete_payee: Payee,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await payee.create_payee(payee=payee_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_payee.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_payee.model_dump()

        # Don't need to test the response here because it's just the updated payee_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(self, user: User, payee_to_create: PayeeCreate, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await payee.create_payee(payee=payee_to_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_payee: Payee) -> PayeeRead:
        return PayeeRead.model_validate(complete_payee)

    @pytest.fixture
    def expected_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_payee")])
    async def test_get_with_data(self, user: User, payee_id: int, mock_db: Mock, expected_sql: str, expected_response: PayeeRead) -> None:
        response = await payee.get_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(self, user: User, payee_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await payee.get_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_payee_found(self, user: User, payee_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any) -> None:
        response = await payee.delete_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_payee_not_found(self, user: User, payee_id: int, mock_db: Mock, expected_sql: str) -> None:
        with pytest.raises(HTTPException):
            await payee.delete_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def payee_updates(self) -> PayeeUpdate:
        return PayeeUpdate(name="some new name")

    @pytest.fixture
    def expected_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_payee(self, complete_payee: Payee) -> Payee:
        return Payee.model_validate(complete_payee.model_dump(), update={"name": "some new name"})

    @pytest.fixture
    def expected_response(self, updated_payee: Payee) -> PayeeRead:
        return PayeeRead.model_validate(updated_payee.model_dump())

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_payee")])
    async def test_update_with_payee_found(
        self,
        user: User,
        payee_id: int,
        payee_updates: PayeeUpdate,
        mock_db: Mock,
        expected_sql: str,
        updated_payee: Payee,
        expected_response: PayeeRead,
    ) -> None:
        response = await payee.update_payee(
            payee_id=payee_id,
            payee=payee_updates,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_payee.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_payee.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_payee_not_found(
        self,
        user: User,
        payee_id: int,
        payee_updates: PayeeUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await payee.update_payee(
                payee_id=payee_id,
                payee=payee_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
