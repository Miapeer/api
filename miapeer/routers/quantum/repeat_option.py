from fastapi import APIRouter, Depends
from sqlmodel import select

from miapeer.dependencies import DbSession, is_quantum_user
from miapeer.models.quantum.repeat_option import RepeatOption, RepeatOptionRead

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
    sql = select(RepeatOption)
    repeat_options = db.exec(sql).all()
    return [RepeatOptionRead.model_validate(repeat_option) for repeat_option in repeat_options]
