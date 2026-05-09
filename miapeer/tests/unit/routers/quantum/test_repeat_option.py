from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.quantum.repeat_option import RepeatOption, RepeatOptionRead
from miapeer.models.quantum.repeat_unit import RepeatUnit, RepeatUnitRead
from miapeer.routers.quantum import repeat_option
from pytest_lazy_fixtures import lf as lazy_fixture

pytestmark = pytest.mark.asyncio


raw_repeat_option_id = 11111
raw_repeat_unit_id = 22222


@pytest.fixture
def repeat_option_id() -> int:
    return raw_repeat_option_id


@pytest.fixture
def repeat_unit_id() -> int:
    return raw_repeat_unit_id


@pytest.fixture
def complete_repeat_option(repeat_option_id: int) -> RepeatOption:
    return RepeatOption(
        repeat_option_id=repeat_option_id,
        name="Weekly",
        repeat_unit_id=1,
        quantity=1,
        order_index=0,
    )


@pytest.fixture
def complete_repeat_unit(repeat_unit_id: int) -> RepeatUnit:
    return RepeatUnit(
        repeat_unit_id=repeat_unit_id,
        name="Week",
    )


class TestGetRepeatOption:
    @pytest.fixture
    def expected_sql(self, repeat_option_id: int) -> str:
        return (
            f"SELECT quantum_repeat_option.name, quantum_repeat_option.repeat_unit_id, "
            f"quantum_repeat_option.quantity, quantum_repeat_option.order_index, quantum_repeat_option.repeat_option_id \n"
            f"FROM quantum_repeat_option \n"
            f"WHERE quantum_repeat_option.repeat_option_id = {repeat_option_id}"
        )

    @pytest.mark.parametrize(
        "db_one_or_none_return_val", [lazy_fixture("complete_repeat_option")]
    )
    async def test_get_repeat_option_with_data(
        self,
        repeat_option_id: int,
        mock_db: Mock,
        expected_sql: str,
        complete_repeat_option: RepeatOption,
    ) -> None:
        response = await repeat_option.get_repeat_option(
            db=mock_db, repeat_option_id=repeat_option_id
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == RepeatOptionRead.model_validate(complete_repeat_option)

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_repeat_option_with_no_data_raises_exception(
        self,
        repeat_option_id: int,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await repeat_option.get_repeat_option(
                db=mock_db, repeat_option_id=repeat_option_id
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql


class TestGetRepeatUnit:
    @pytest.fixture
    def expected_sql(self, repeat_unit_id: int) -> str:
        return (
            f"SELECT quantum_repeat_unit.name, quantum_repeat_unit.repeat_unit_id \n"
            f"FROM quantum_repeat_unit \n"
            f"WHERE quantum_repeat_unit.repeat_unit_id = {repeat_unit_id}"
        )

    @pytest.mark.parametrize(
        "db_one_or_none_return_val", [lazy_fixture("complete_repeat_unit")]
    )
    async def test_get_repeat_unit_with_data(
        self,
        repeat_unit_id: int,
        mock_db: Mock,
        expected_sql: str,
        complete_repeat_unit: RepeatUnit,
    ) -> None:
        response = await repeat_option.get_repeat_unit(
            db=mock_db, repeat_unit_id=repeat_unit_id
        )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == RepeatUnitRead.model_validate(complete_repeat_unit)

    @pytest.mark.parametrize("db_one_or_none_return_val", [None, []])
    async def test_get_repeat_unit_with_no_data_raises_exception(
        self,
        repeat_unit_id: int,
        mock_db: Mock,
        expected_sql: str,
    ) -> None:
        with pytest.raises(HTTPException):
            await repeat_option.get_repeat_unit(
                db=mock_db, repeat_unit_id=repeat_unit_id
            )

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
