from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from miapeer.dependencies import DbSession, is_miapeer_super_user
from miapeer.models.miapeer import (
    Application,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(
    prefix="/applications",
    tags=["Miapeer: Applications"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_all_applications(
    db: DbSession,
) -> list[ApplicationRead]:
    applications = db.exec(select(Application).order_by(Application.name)).all()
    return [ApplicationRead.model_validate(application) for application in applications]


@router.post(
    "",
    dependencies=[Depends(is_miapeer_super_user)],
)
async def create_application(
    db: DbSession,
    application: ApplicationCreate,
) -> ApplicationRead:
    db_application = Application.model_validate(application)
    db.add(db_application)
    # TODO: Add application roles
    db.commit()
    db.refresh(db_application)
    return ApplicationRead.model_validate(db_application)


@router.get("/{application_id}")
async def get_application(db: DbSession, application_id: int) -> ApplicationRead:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationRead.model_validate(application)


@router.delete("/{application_id}", dependencies=[Depends(is_miapeer_super_user)])
async def delete_application(db: DbSession, application_id: int) -> dict[str, bool]:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{application_id}",
    dependencies=[Depends(is_miapeer_super_user)],
)
async def update_application(
    db: DbSession,
    application_id: int,
    application: ApplicationUpdate,
) -> ApplicationRead:
    db_application = db.get(Application, application_id)

    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    updated_application = Application.model_validate(db_application.model_dump(), update=application.model_dump())

    db.add(updated_application)
    db.commit()
    db.refresh(updated_application)

    return ApplicationRead.model_validate(updated_application)
