from fastapi import APIRouter

router = APIRouter(
    prefix="/permissions",
    tags=["Miapeer API"],
    # dependencies=[Depends(is_authorized)],
    responses={404: {"description": "Not found"}},
)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

from miapeer.adapter.database import engine
from miapeer.dependencies import get_session
from miapeer.models.permission import (
    Permission,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from miapeer.routers.miapeer_api.permission import router


@router.get("/", response_model=list[PermissionRead])
async def get_all_permissions(
    session: Session = Depends(get_session),
) -> list[Permission]:
    permissions = session.exec(select(Permission)).all()
    return permissions


@router.post("/", response_model=PermissionRead)
async def create_permission(
    permission: PermissionCreate,
    session: Session = Depends(get_session),
) -> Permission:
    db_permission = Permission.from_orm(permission)
    session.add(db_permission)
    session.commit()
    session.refresh(db_permission)
    return db_permission


@router.get("/{permission_id}", response_model=Permission)
async def get_permission(permission_id: int, session: Session = Depends(get_session)) -> Permission:
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.delete("/{permission_id}")
def delete_permission(permission_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    session.delete(permission)
    session.commit()
    return {"ok": True}


@router.patch("/{permission_id}", response_model=PermissionRead)
def update_permission(
    permission_id: int,
    permission: PermissionUpdate,
    session: Session = Depends(get_session),
) -> Permission:
    db_permission = session.get(Permission, permission_id)
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    permission_data = permission.dict(exclude_unset=True)

    for key, value in permission_data.items():
        setattr(db_permission, key, value)

    session.add(db_permission)
    session.commit()
    session.refresh(db_permission)
    return db_permission
