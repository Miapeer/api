from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import get_db, is_miapeer_admin
from miapeer.models.miapeer.permission import (
    Permission,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)

router = APIRouter(
    prefix="/permissions",
    tags=["Miapeer: Permissions"],
    dependencies=[Depends(is_miapeer_admin)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[PermissionRead])
async def get_all_permissions(
    db: Session = Depends(get_db),
) -> list[Permission]:
    permissions = db.exec(select(Permission)).all()
    return permissions


# TODO: Should only be able to modify permissions lower than your level
@router.post("/", response_model=PermissionRead)
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
) -> Permission:
    db_permission = Permission.from_orm(permission)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


@router.get("/{permission_id}", response_model=PermissionRead)
async def get_permission(permission_id: int, db: Session = Depends(get_db)) -> Permission:
    permission = db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.delete("/{permission_id}")
def delete_permission(permission_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    permission = db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return {"ok": True}


@router.patch("/{permission_id}", response_model=PermissionRead)
def update_permission(
    permission_id: int,
    permission: PermissionUpdate,
    db: Session = Depends(get_db),
) -> Permission:
    db_permission = db.get(Permission, permission_id)
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    permission_data = permission.dict(exclude_unset=True)

    for key, value in permission_data.items():
        setattr(db_permission, key, value)

    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission
