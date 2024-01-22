from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import get_db, is_miapeer_super_user
from miapeer.models.miapeer import (
    ApplicationRole,
    ApplicationRoleCreate,
    ApplicationRoleRead,
)

router = APIRouter(
    prefix="/application-roles",
    tags=["Miapeer: Application-Roles"],
    dependencies=[Depends(is_miapeer_super_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ApplicationRoleRead])
async def get_all_application_roles(
    db: Session = Depends(get_db),
) -> list[ApplicationRole]:
    application_roles = db.exec(select(ApplicationRole)).all()

    return application_roles


# TODO: Should this even be exposed?
@router.post("/", response_model=ApplicationRoleRead)
async def create_application_role(
    application_role: ApplicationRoleCreate,
    db: Session = Depends(get_db),
    # commons: dict = Depends(is_zomething)
) -> ApplicationRole:
    db_application_role = ApplicationRole.from_orm(application_role)
    db.add(db_application_role)
    db.commit()
    db.refresh(db_application_role)
    return db_application_role


@router.get("/{application_role_id}", response_model=ApplicationRoleRead)
async def get_application_role(application_role_id: int, db: Session = Depends(get_db)) -> ApplicationRole:
    application_role = db.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    return application_role


# TODO: Should this even be exposed?
@router.delete("/{application_role_id}")
async def delete_application_role(application_role_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    application_role = db.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    db.delete(application_role)
    db.commit()
    return {"ok": True}
