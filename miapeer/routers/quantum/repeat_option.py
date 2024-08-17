from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import asc, select

from miapeer.dependencies import DbSession, is_quantum_user
from miapeer.models.quantum.repeat_option import RepeatOption, RepeatOptionRead
from miapeer.models.quantum.repeat_unit import RepeatUnit, RepeatUnitRead

router = APIRouter(
    prefix="/repeat-options",
    tags=["Quantum: Repeat Options"],
    dependencies=[Depends(is_quantum_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_all_repeat_options(
    db: DbSession,
) -> list[RepeatOptionRead]:
    sql = select(RepeatOption).order_by(asc(RepeatOption.order_index))
    repeat_options = db.exec(sql).all()
    return [RepeatOptionRead.model_validate(repeat_option) for repeat_option in repeat_options]


async def get_repeat_option(
    db: DbSession,
    repeat_option_id: int,
) -> RepeatOptionRead:

    sql = select(RepeatOption).where(RepeatOption.repeat_option_id == repeat_option_id)
    repeat_option = db.exec(sql).one_or_none()

    if not repeat_option:
        raise HTTPException(status_code=404, detail="Repeat Option not found")

    return RepeatOptionRead.model_validate(repeat_option)


async def get_repeat_unit(
    db: DbSession,
    repeat_unit_id: int,
) -> RepeatUnitRead:

    sql = select(RepeatUnit).where(RepeatUnit.repeat_unit_id == repeat_unit_id)
    repeat_unit = db.exec(sql).one_or_none()

    if not repeat_unit:
        raise HTTPException(status_code=404, detail="Repeat Unit not found")

    return RepeatUnitRead.model_validate(repeat_unit)
