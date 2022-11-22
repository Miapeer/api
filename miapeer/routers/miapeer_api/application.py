from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import get_session, is_miapeer_super_user
from miapeer.models.application import (
    Application,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(
    prefix="/applications",
    tags=["Miapeer API: Applications"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ApplicationRead])
async def get_all_applications(
    session: Session = Depends(get_session),
) -> list[Application]:
    applications = session.exec(select(Application).order_by(Application.name)).all()
    return applications


@router.post("/", dependencies=[Depends(is_miapeer_super_user)], response_model=ApplicationRead)
async def create_application(
    application: ApplicationCreate,
    session: Session = Depends(get_session),
) -> Application:
    db_application = Application.from_orm(application)
    session.add(db_application)
    # TODO: Add application roles
    session.commit()
    session.refresh(db_application)
    return db_application


@router.get("/{application_id}", response_model=Application)
async def get_application(application_id: int, session: Session = Depends(get_session)) -> Application:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.delete("/{application_id}", dependencies=[Depends(is_miapeer_super_user)])
def delete_application(application_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    session.delete(application)
    session.commit()
    return {"ok": True}


@router.patch("/{application_id}", dependencies=[Depends(is_miapeer_super_user)], response_model=ApplicationRead)
def update_application(
    application_id: int,
    application: ApplicationUpdate,
    session: Session = Depends(get_session),
) -> Application:
    db_application = session.get(Application, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    application_data = application.dict(exclude_unset=True)

    for key, value in application_data.items():
        setattr(db_application, key, value)

    session.add(db_application)
    session.commit()
    session.refresh(db_application)
    return db_application
