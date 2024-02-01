from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import (
    CurrentUser,
    DbSession,
    is_miapeer_admin,
    is_miapeer_super_user,
)
from miapeer.models.miapeer import User, UserCreate, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Miapeer: Users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me")
async def who_am_i(current_user: CurrentUser) -> User:
    return current_user


@router.get(
    "/",
    dependencies=[Depends(is_miapeer_admin)],
)
async def get_all_users(
    db: DbSession,
) -> list[UserRead]:
    users = db.exec(select(User)).all()
    return [UserRead.model_validate(user) for user in users]


@router.post(
    "/",
    dependencies=[Depends(is_miapeer_admin)],
)
async def create_user(
    db: DbSession,
    user: UserCreate,
) -> UserRead:
    user_data = user.model_dump()
    user_data["password"] = ""
    user_data["disabled"] = False

    db_user = User.model_validate(user_data)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserRead.model_validate(db_user)


@router.get(
    "/{user_id}",
    dependencies=[Depends(is_miapeer_admin)],
)
async def get_user(db: DbSession, user_id: int) -> UserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.delete("/{user_id}", dependencies=[Depends(is_miapeer_super_user)])
async def delete_user(db: DbSession, user_id: int) -> dict[str, bool]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{user_id}",
    dependencies=[Depends(is_miapeer_super_user)],
)
async def update_user(
    db: DbSession,
    user_id: int,
    user: UserUpdate,
) -> UserRead:
    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = User.model_validate(db_user.model_dump(), update=user.model_dump())

    db.add(updated_user)
    db.commit()
    db.refresh(updated_user)

    return UserRead.model_validate(updated_user)
