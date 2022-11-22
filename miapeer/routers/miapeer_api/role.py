from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_session,
    is_miapeer_admin,
    is_miapeer_super_user,
)
from miapeer.models.role import Role, RoleCreate, RoleRead, RoleUpdate

router = APIRouter(
    prefix="/roles",
    tags=["Miapeer API: Roles"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(is_miapeer_admin)], response_model=list[RoleRead])
async def get_all_roles(
    session: Session = Depends(get_session),
) -> list[Role]:
    roles = session.exec(select(Role)).all()
    return roles


@router.post("/", dependencies=[Depends(is_miapeer_super_user)], response_model=RoleRead)
async def create_role(
    role: RoleCreate,
    session: Session = Depends(get_session),
) -> Role:
    db_role = Role.from_orm(role)
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


@router.get("/{role_id}", dependencies=[Depends(is_miapeer_admin)], response_model=Role)
async def get_role(role_id: int, session: Session = Depends(get_session)) -> Role:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}", dependencies=[Depends(is_miapeer_super_user)])
def delete_role(role_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    session.delete(role)
    session.commit()
    return {"ok": True}


@router.patch("/{role_id}", dependencies=[Depends(is_miapeer_super_user)], response_model=RoleRead)
def update_role(
    role_id: int,
    role: RoleUpdate,
    session: Session = Depends(get_session),
) -> Role:
    db_role = session.get(Role, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    role_data = role.dict(exclude_unset=True)

    for key, value in role_data.items():
        setattr(db_role, key, value)

    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role
