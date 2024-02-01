from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pytest_lazyfixture import lazy_fixture

from miapeer.models.miapeer import User
from miapeer.models.quantum.transaction_type import (
    TransactionType,
    TransactionTypeCreate,
    TransactionTypeRead,
    TransactionTypeUpdate,
)
from miapeer.routers.quantum import transaction_type

pytestmark = pytest.mark.asyncio

raw_transaction_type_id = 12345


@pytest.fixture
def transaction_type_id() -> int:
    return raw_transaction_type_id


@pytest.fixture
def transaction_type_name() -> str:
    return "transaction type name"


@pytest.fixture
def portfolio_id() -> int:
    return 321


@pytest.fixture
def basic_transaction_type(transaction_type_name: str, portfolio_id: int) -> TransactionType:
    return TransactionType(transaction_type_id=None, name=transaction_type_name, portfolio_id=portfolio_id)


@pytest.fixture
def complete_transaction_type(transaction_type_id: int, basic_transaction_type: TransactionType) -> TransactionType:
    return TransactionType.model_validate(
        basic_transaction_type.model_dump(), update={"transaction_type_id": transaction_type_id}
    )


class TestGetAll:
    @pytest.fixture
    def multiple_transaction_types(self, complete_transaction_type: TransactionType) -> list[TransactionType]:
        return [complete_transaction_type, complete_transaction_type]

    @pytest.fixture
    def expected_multiple_transaction_types(
        self, complete_transaction_type: TransactionType
    ) -> list[TransactionTypeRead]:
        working_transaction_type = TransactionTypeRead.model_validate(complete_transaction_type)
        return [working_transaction_type, working_transaction_type]

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (lazy_fixture("multiple_transaction_types"), lazy_fixture("expected_multiple_transaction_types"))],
    )
    async def test_get_all(
        self, user: User, mock_db: Mock, expected_sql: str, expected_response: list[TransactionTypeRead]
    ) -> None:
        response = await transaction_type.get_all_transaction_types(db=mock_db, current_user=user)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:
        obj.transaction_type_id = raw_transaction_type_id

    @pytest.fixture
    def transaction_type_to_create(self, transaction_type_name: str, portfolio_id: int) -> TransactionTypeCreate:
        return TransactionTypeCreate(name=transaction_type_name, portfolio_id=portfolio_id)

    @pytest.fixture
    def expected_sql(self, user_id: int) -> str:
        return f"SELECT quantum_portfolio.portfolio_id \nFROM quantum_portfolio JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create_with_portfolio_found(
        self,
        user: User,
        transaction_type_to_create: TransactionTypeCreate,
        complete_transaction_type: TransactionType,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:

        await transaction_type.create_transaction_type(
            transaction_type=transaction_type_to_create, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_transaction_type.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_transaction_type.model_dump()

        # Don't need to test the response here because it's just the updated transaction_type_to_add

    @pytest.mark.parametrize("db_first_return_val", [None, ""])
    async def test_create_with_portfolio_not_found(
        self, user: User, transaction_type_to_create: TransactionTypeCreate, mock_db: Mock, expected_sql: str
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.create_transaction_type(
                transaction_type=transaction_type_to_create, db=mock_db, current_user=user
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_transaction_type: TransactionType) -> TransactionTypeRead:
        return TransactionTypeRead.model_validate(complete_transaction_type)

    @pytest.fixture
    def expected_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_transaction_type")])
    async def test_get_with_data(
        self,
        user: User,
        transaction_type_id: int,
        mock_db: Mock,
        expected_sql: str,
        expected_response: TransactionTypeRead,
    ) -> None:
        response = await transaction_type.get_transaction_type(
            transaction_type_id=transaction_type_id, db=mock_db, current_user=user
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response

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
    def transaction_type_updates(self) -> TransactionTypeUpdate:
        return TransactionTypeUpdate(name="some new name")

    @pytest.fixture
    def expected_sql(self, user_id: int, transaction_type_id: int) -> str:
        return f"SELECT quantum_transaction_type.name, quantum_transaction_type.portfolio_id, quantum_transaction_type.transaction_type_id \nFROM quantum_transaction_type JOIN quantum_portfolio ON quantum_portfolio.portfolio_id = quantum_transaction_type.portfolio_id JOIN quantum_portfolio_user ON quantum_portfolio.portfolio_id = quantum_portfolio_user.portfolio_id \nWHERE quantum_transaction_type.transaction_type_id = {transaction_type_id} AND quantum_portfolio_user.user_id = {user_id}"

    @pytest.fixture
    def updated_transaction_type(self, complete_transaction_type: TransactionType) -> TransactionType:
        return TransactionType.model_validate(complete_transaction_type.model_dump(), update={"name": "some new name"})

    @pytest.fixture
    def expected_response(self, updated_transaction_type: TransactionType) -> TransactionTypeRead:
        return TransactionTypeRead.model_validate(updated_transaction_type.model_dump())

    @pytest.mark.parametrize("db_one_or_none_return_val", [lazy_fixture("complete_transaction_type")])
    async def test_update_with_transaction_type_found(
        self,
        user: User,
        transaction_type_id: int,
        transaction_type_updates: TransactionTypeUpdate,
        mock_db: Mock,
        expected_sql: str,
        updated_transaction_type: TransactionType,
        expected_response: TransactionTypeRead,
    ) -> None:
        response = await transaction_type.update_transaction_type(
            transaction_type_id=transaction_type_id,
            transaction_type=transaction_type_updates,
            db=mock_db,
            current_user=user,
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_transaction_type.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_transaction_type.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_update_with_transaction_type_not_found(
        self,
        user: User,
        transaction_type_id: int,
        transaction_type_updates: TransactionTypeUpdate,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await transaction_type.update_transaction_type(
                transaction_type_id=transaction_type_id,
                transaction_type=transaction_type_updates,
                db=mock_db,
                current_user=user,
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
