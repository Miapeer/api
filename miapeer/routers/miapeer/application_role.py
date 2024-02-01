from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import DbSession, is_miapeer_super_user
from miapeer.models.miapeer import (
    ApplicationRole,
    ApplicationRoleCreate,
    ApplicationRoleRead,
    ApplicationRoleUpdate,
)

router = APIRouter(
    prefix="/application-roles",
    tags=["Miapeer: Application-Roles"],
    dependencies=[Depends(is_miapeer_super_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_all_application_roles(
    db: DbSession,
) -> list[ApplicationRoleRead]:
    application_roles = db.exec(select(ApplicationRole)).all()
    return [ApplicationRoleRead.model_validate(application_role) for application_role in application_roles]


# TODO: Should this even be exposed?
@router.post("/")
async def create_application_role(
    db: DbSession,
    application_role: ApplicationRoleCreate,
) -> ApplicationRoleRead:
    db_application_role = ApplicationRole.model_validate(application_role)

    db.add(db_application_role)
    db.commit()
    db.refresh(db_application_role)

    return ApplicationRoleRead.model_validate(db_application_role)


@router.get("/{application_role_id}")
async def get_application_role(db: DbSession, application_role_id: int) -> ApplicationRoleRead:
    application_role = db.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    return ApplicationRoleRead.model_validate(application_role)


# TODO: Should this even be exposed?
@router.delete("/{application_role_id}")
async def delete_application_role(db: DbSession, application_role_id: int) -> dict[str, bool]:
    application_role = db.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    db.delete(application_role)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{application_role_id}",
)
async def update_application_role(
    db: DbSession,
    application_role_id: int,
    application_role: ApplicationRoleUpdate,
) -> ApplicationRoleRead:
    db_application_role = db.get(ApplicationRole, application_role_id)

    if not db_application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")

    application_role_data = application_role.model_dump(exclude_unset=True)

    for key, value in application_role_data.items():
        setattr(db_application_role, key, value)

    db.add(db_application_role)
    db.commit()
    db.refresh(db_application_role)

    return ApplicationRoleRead.model_validate(db_application_role)
