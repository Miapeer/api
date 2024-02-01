from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import DbSession, is_miapeer_admin
from miapeer.models.miapeer import Permission, PermissionCreate, PermissionRead

router = APIRouter(
    prefix="/permissions",
    tags=["Miapeer: Permissions"],
    dependencies=[Depends(is_miapeer_admin)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_all_permissions(
    db: DbSession,
) -> list[PermissionRead]:
    permissions = db.exec(select(Permission)).all()
    return [PermissionRead.model_validate(permission) for permission in permissions]


# TODO: Should only be able to modify permissions lower than your level
@router.post("/")
async def create_permission(
    db: DbSession,
    permission: PermissionCreate,
) -> PermissionRead:
    db_permission = Permission.model_validate(permission)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return PermissionRead.model_validate(db_permission)


@router.get("/{permission_id}")
async def get_permission(db: DbSession, permission_id: int) -> PermissionRead:
    permission = db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return PermissionRead.model_validate(permission)


@router.delete("/{permission_id}")
async def delete_permission(db: DbSession, permission_id: int) -> dict[str, bool]:
    permission = db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return {"ok": True}
