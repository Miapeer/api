from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.payee import Payee, PayeeCreate, PayeeUpdate
from miapeer.routers.quantum import payee

pytestmark = pytest.mark.asyncio


@pytest.fixture
def payee_id() -> int:
    return 12345


@pytest.fixture
def payee_name() -> str:
    return "transaction type name"


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await payee.get_all_payees(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def payee_create(self, payee_name: str, portfolio_id: int) -> PayeeCreate:
        return PayeeCreate(name=payee_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def payee_to_add(self, payee_name: str, portfolio_id: int) -> Payee:
        return Payee(payee_id=None, name=payee_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        payee_create: PayeeCreate,
        payee_to_add: Payee,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await payee.create_payee(payee=payee_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(payee_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(payee_to_add)
        # Don't need to test the response here because it's just the updated payee_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, payee_create: PayeeCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await payee.create_payee(payee=payee_create, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self, user: User, payee_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await payee.get_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

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
    async def test_delete_with_payee_found(
        self, user: User, payee_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await payee.delete_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_payee_not_found(
        self, user: User, payee_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await payee.delete_payee(payee_id=payee_id, db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def payee(self, payee_name: str, portfolio_id: int) -> Payee:
        return Payee(payee_id=None, name=payee_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def updated_payee(self) -> PayeeUpdate:
        return PayeeUpdate(name="some new name")

    @pytest.fixture
    def expected_sql(self, user_id: int, payee_id: int) -> str:
        return f"SELECT quantum_payee.name, quantum_payee.portfolio_id, quantum_payee.payee_id \nFROM quantum_payee JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_payee.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_payee.payee_id = {payee_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [payee])
    async def test_update_with_payee_found(
        self,
        user: User,
        payee_id: int,
        updated_payee: PayeeUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: Payee,
    ) -> None:
        response = await payee.update_payee(
            payee_id=payee_id,
            payee=updated_payee,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_one_or_none_return_val)
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_payee_not_found(
        self,
        user: User,
        payee_id: int,
        updated_payee: PayeeUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await payee.update_payee(
                payee_id=payee_id,
                payee=updated_payee,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
