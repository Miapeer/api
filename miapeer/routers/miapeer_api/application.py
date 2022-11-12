from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

from miapeer.adapter.database import engine
from miapeer.dependencies import get_session, is_authorized, is_zomething
from miapeer.models.application import (
    Application,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(
    prefix="/miapeer/v1/applications",
    tags=["miapeer"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ApplicationRead])
async def get_all_applications(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
) -> list[Application]:
    applications = session.exec(
        select(Application)  # .order_by(text("name")).offset(offset).limit(limit)
    ).all()
    return applications


# TODO: Should this even be exposed?
@router.post("/", response_model=ApplicationRead)
async def create_application(
    application: ApplicationCreate,
    session: Session = Depends(get_session),
    # commons: dict = Depends(is_zomething)
) -> Application:
    db_application = Application.from_orm(application)
    session.add(db_application)
    session.commit()
    session.refresh(db_application)
    return db_application


@router.get("/{application_id}", response_model=Application)
async def get_application(
    application_id: int, session: Session = Depends(get_session)
) -> Application:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


# TODO: Should this even be exposed?
@router.delete("/{application_id}")
def delete_application(
    application_id: int, session: Session = Depends(get_session)
) -> dict[str, bool]:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    session.delete(application)
    session.commit()
    return {"ok": True}


@router.patch("/{application_id}", response_model=ApplicationRead)
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


# @app.get("/heroes/{hero_id}", response_model=HeroReadWithTeam)
# def read_hero(*, session: Session = Depends(get_session), hero_id: int):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero

# @app.get("/teams/{team_id}", response_model=TeamReadWithHeroes)
# def read_team(*, team_id: int, session: Session = Depends(get_session)):
#     team = session.get(Team, team_id)
#     if not team:
#         raise HTTPException(status_code=404, detail="Team not found")
#     return team


# @app.post("/heroes/")
# def create_hero(hero: Hero):
#     with Session(engine) as session:
#         session.add(hero)
#         session.commit()
#         session.refresh(hero)
#         return hero


# @router.put(
#     "/{item_id}",
#     tags=["custom"],
#     responses={403: {"description": "Operation forbidden"}},
# )
# async def update_item(item_id: str):
#     if item_id != "plumbus":
#         raise HTTPException(
#             status_code=403, detail="You can only update the item: plumbus"
#         )
#     return {"item_id": item_id, "name": "The great Plumbus"}


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)


# @app.get("/users/", response_model=list[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user


# @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=list[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items
