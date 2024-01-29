from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_db,
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
    "/",
    dependencies=[Depends(is_miapeer_admin)],
    response_model=list[RoleRead],
)
async def get_all_roles(
    db: Session = Depends(get_db),
) -> list[Role]:
    roles = list(db.exec(select(Role)).all())
    return roles


@router.post(
    "/",
    dependencies=[Depends(is_miapeer_super_user)],
    response_model=RoleRead,
)
async def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
) -> Role:
    db_role = Role.model_validate(role)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@router.get(
    "/{role_id}",
    dependencies=[Depends(is_miapeer_admin)],
    response_model=Role,
)
async def get_role(role_id: int, db: Session = Depends(get_db)) -> Role:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}", dependencies=[Depends(is_miapeer_super_user)])
async def delete_role(role_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{role_id}",
    dependencies=[Depends(is_miapeer_super_user)],
    response_model=RoleRead,
)
async def update_role(
    role_id: int,
    role: RoleUpdate,
    db: Session = Depends(get_db),
) -> Role:
    db_role = db.get(Role, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    role_data = role.model_dump(exclude_unset=True)

    for key, value in role_data.items():
        setattr(db_role, key, value)

    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role
