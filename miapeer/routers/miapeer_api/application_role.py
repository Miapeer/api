from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import get_session, is_miapeer_super_user
from miapeer.models.application_role import (
    ApplicationRole,
    ApplicationRoleCreate,
    ApplicationRoleRead,
    ApplicationRoleUpdate,
)

router = APIRouter(
    prefix="/application_roles",
    tags=["Miapeer API: Application-Roles"],
    dependencies=[Depends(is_miapeer_super_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ApplicationRoleRead])
async def get_all_application_roles(
    session: Session = Depends(get_session),
) -> list[ApplicationRole]:
    application_roles = session.exec(select(ApplicationRole)).all()
    return application_roles


# TODO: Should this even be exposed?
@router.post("/", response_model=ApplicationRoleRead)
async def create_application_role(
    application_role: ApplicationRoleCreate,
    session: Session = Depends(get_session),
    # commons: dict = Depends(is_zomething)
) -> ApplicationRole:
    db_application_role = ApplicationRole.from_orm(application_role)
    session.add(db_application_role)
    session.commit()
    session.refresh(db_application_role)
    return db_application_role


@router.get("/{application_role_id}", response_model=ApplicationRole)
async def get_application_role(application_role_id: int, session: Session = Depends(get_session)) -> ApplicationRole:
    application_role = session.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    return application_role


# TODO: Should this even be exposed?
@router.delete("/{application_role_id}")
def delete_application_role(application_role_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    application_role = session.get(ApplicationRole, application_role_id)
    if not application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")
    session.delete(application_role)
    session.commit()
    return {"ok": True}


@router.patch("/{application_role_id}", response_model=ApplicationRoleRead)
def update_application_role(
    application_role_id: int,
    application_role: ApplicationRoleUpdate,
    session: Session = Depends(get_session),
) -> ApplicationRole:
    db_application_role = session.get(ApplicationRole, application_role_id)
    if not db_application_role:
        raise HTTPException(status_code=404, detail="Application Role not found")

    application_role_data = application_role.dict(exclude_unset=True)

    for key, value in application_role_data.items():
        setattr(db_application_role, key, value)

    session.add(db_application_role)
    session.commit()
    session.refresh(db_application_role)
    return db_application_role
