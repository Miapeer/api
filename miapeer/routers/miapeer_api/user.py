from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Miapeer API"],
    # dependencies=[Depends(is_authorized)],
    responses={404: {"description": "Not found"}},
)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

from miapeer.adapter.database import engine
from miapeer.dependencies import get_current_active_user, get_session
from miapeer.models.user import User, UserCreate, UserRead, UserUpdate
from miapeer.routers.miapeer_api.user import router


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.get("/", response_model=list[UserRead])
async def get_all_users(
    session: Session = Depends(get_session),
) -> list[User]:
    users = session.exec(select(User)).all()
    return users


@router.post("/", response_model=UserRead)
async def create_user(
    user: UserCreate,
    session: Session = Depends(get_session),
) -> User:
    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user: UserUpdate,
    session: Session = Depends(get_session),
) -> User:
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.dict(exclude_unset=True)

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
