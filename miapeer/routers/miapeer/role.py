from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import (
    DbSession,
    is_miapeer_admin,
    is_miapeer_super_user,
)
from miapeer.models.miapeer import Role, RoleCreate, RoleRead, RoleUpdate

router = APIRouter(
    prefix="/roles",
    tags=["Miapeer: Roles"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    dependencies=[Depends(is_miapeer_admin)],
)
async def get_all_roles(
    db: DbSession,
) -> list[RoleRead]:
    roles = db.exec(select(Role)).all()
    return [RoleRead.model_validate(role) for role in roles]


@router.post(
    "",
    dependencies=[Depends(is_miapeer_super_user)],
)
async def create_role(
    db: DbSession,
    role: RoleCreate,
) -> RoleRead:
    db_role = Role.model_validate(role)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return RoleRead.model_validate(db_role)


@router.get(
    "/{role_id}",
    dependencies=[Depends(is_miapeer_admin)],
)
async def get_role(db: DbSession, role_id: int) -> RoleRead:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleRead.model_validate(role)


@router.delete("/{role_id}", dependencies=[Depends(is_miapeer_super_user)])
async def delete_role(db: DbSession, role_id: int) -> dict[str, bool]:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{role_id}",
    dependencies=[Depends(is_miapeer_super_user)],
)
async def update_role(
    db: DbSession,
    role_id: int,
    role: RoleUpdate,
) -> RoleRead:
    db_role = db.get(Role, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    updated_role = Role.model_validate(db_role.model_dump(), update=role.model_dump())

    db.add(updated_role)
    db.commit()
    db.refresh(updated_role)
    return RoleRead.model_validate(updated_role)
