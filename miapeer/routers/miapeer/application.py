from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import get_db, is_miapeer_super_user
from miapeer.models.miapeer.application import (
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


@router.get("/", response_model=list[ApplicationRead])
async def get_all_applications(
    db: Session = Depends(get_db),
) -> list[Application]:
    applications = db.exec(select(Application).order_by(Application.name)).all()
    return applications


@router.post(
    "/",
    dependencies=[Depends(is_miapeer_super_user)],
    response_model=ApplicationRead,
)
async def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
) -> Application:
    db_application = Application.from_orm(application)
    db.add(db_application)
    # TODO: Add application roles
    db.commit()
    db.refresh(db_application)
    return db_application


@router.get("/{application_id}", response_model=Application)
async def get_application(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.delete("/{application_id}", dependencies=[Depends(is_miapeer_super_user)])
def delete_application(application_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return {"ok": True}


@router.patch(
    "/{application_id}",
    dependencies=[Depends(is_miapeer_super_user)],
    response_model=ApplicationRead,
)
def update_application(
    application_id: int,
    application: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> Application:
    db_application = db.get(Application, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    application_data = application.dict(exclude_unset=True)

    for key, value in application_data.items():
        setattr(db_application, key, value)

    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application
