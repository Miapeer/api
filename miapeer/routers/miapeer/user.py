from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import (
    CurrentUser,
    DbSession,
    is_miapeer_admin,
    is_miapeer_super_user,
)
from miapeer.models.miapeer import (
    Application,
    ApplicationRole,
    Permission,
    Role,
    User,
    UserCreate,
    UserRead,
    UserUpdate,
)
from miapeer.routers.auth import get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["Miapeer: Users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me")
async def who_am_i(current_user: CurrentUser) -> User:
    return current_user


@router.get(
    "",
    dependencies=[Depends(is_miapeer_admin)],
)
async def get_all_users(
    db: DbSession,
) -> list[UserRead]:
    users = db.exec(select(User)).all()
    return [UserRead.model_validate(user) for user in users]


@router.post("")
async def create_user(
    db: DbSession,
    user: UserCreate,
) -> UserRead:

    # Create the user
    db_user = User.model_validate(user.model_dump(), update={"password": get_password_hash(user.password)})

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Add Quantum as initial permissions
    application_role_sql = select(ApplicationRole).join(Application).join(Role).where(Application.name == "Quantum").where(Role.name == "User")
    application_role_found = db.exec(application_role_sql).first()
    if not application_role_found:
        raise HTTPException(status_code=404, detail="ApplicationRole not found")

    if not db_user.user_id or not application_role_found.application_role_id:
        raise HTTPException(status_code=500, detail="Database inconsistent")

    quantum_permission = Permission(user_id=db_user.user_id, application_role_id=application_role_found.application_role_id)
    db.add(quantum_permission)
    db.commit()

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

    password = {"password": get_password_hash(user.password) if user.password else db_user.password}
    updated_user = User.model_validate(db_user.model_dump(), update={**user.model_dump(), **password})

    db.add(updated_user)
    db.commit()
    db.refresh(updated_user)

    return UserRead.model_validate(updated_user)
