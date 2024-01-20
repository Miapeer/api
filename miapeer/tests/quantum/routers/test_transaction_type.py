from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import User
from miapeer.models.quantum.transaction_type import (
    TransactionType,
    TransactionTypeCreate,
    TransactionTypeUpdate,
)
from miapeer.routers.quantum import transaction_type

pytestmark = pytest.mark.asyncio


@pytest.fixture
def transaction_type_id() -> int:
    return 12345


@pytest.fixture
def transaction_type_name() -> str:
    return "transaction type name"


@pytest.fixture
def portfolio_id() -> int:
    return 321


class TestGetAll:
    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, user: User, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await transaction_type.get_all_transaction_types(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def transaction_type_create(self, transaction_type_name: str, portfolio_id: int) -> TransactionTypeCreate:
        return TransactionTypeCreate(name=transaction_type_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def transaction_type_to_add(self, transaction_type_name: str, portfolio_id: int) -> TransactionType:
        return TransactionType(transaction_type_id=None, name=transaction_type_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        transaction_type_create: TransactionTypeCreate,
        transaction_type_to_add: TransactionType,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        await transaction_type.create_transaction_type(
            transaction_type=transaction_type_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_called_once_with(transaction_type_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(transaction_type_to_add)
        # Don't need to test the response here because it's just the updated transaction_type_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, transaction_type_create: TransactionTypeCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.create_transaction_type(
                transaction_type=transaction_type_create, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_get_with_data(
        self, user: User, transaction_type_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await transaction_type.get_transaction_type(
            transaction_type_id=transaction_type_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_one_or_none_return_val

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_with_no_data(
        self, user: User, transaction_type_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.get_transaction_type(
                transaction_type_id=transaction_type_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestDelete:
    @pytest.fixture
    def expected_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", ["some data", 123])
    async def test_delete_with_transaction_type_found(
        self, user: User, transaction_type_id: int, mock_db: Mock, expected_sql: str, db_one_or_none_return_val: Any
    ) -> None:
        response = await transaction_type.delete_transaction_type(
            transaction_type_id=transaction_type_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_called_once_with(db_one_or_none_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_delete_with_transaction_type_not_found(
        self, user: User, transaction_type_id: int, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.delete_transaction_type(
                transaction_type_id=transaction_type_id, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def transaction_type(self) -> TransactionType:
        return TransactionType(transaction_type_id=None, name="transaction type name", portfolio_id=23541)

    @pytest.fixture
    def updated_transaction_type(self) -> TransactionTypeUpdate:
        return TransactionTypeUpdate(name="333")

    @pytest.fixture
    def expected_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [transaction_type])
    async def test_update_with_transaction_type_found(
        self,
        user: User,
        transaction_type_id: int,
        updated_transaction_type: TransactionTypeUpdate,
        mock_db: Mock,
        expected_sql: str,
        db_one_or_none_return_val: TransactionType,
    ) -> None:
        response = await transaction_type.update_transaction_type(
            transaction_type_id=transaction_type_id,
            transaction_type=updated_transaction_type,
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
    async def test_update_with_transaction_type_not_found(
        self,
        user: User,
        transaction_type_id: int,
        updated_transaction_type: TransactionTypeUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.update_transaction_type(
                transaction_type_id=transaction_type_id,
                transaction_type=updated_transaction_type,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
