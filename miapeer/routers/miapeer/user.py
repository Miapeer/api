from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from miapeer.dependencies import (
    get_current_user,
    get_db,
    is_miapeer_admin,
    is_miapeer_super_user,
)
from miapeer.models.miapeer.user import User, UserCreate, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Miapeer: Users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me")
async def who_am_i(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/", dependencies=[Depends(is_miapeer_admin)], response_model=list[UserRead])
async def get_all_users(
    db: Session = Depends(get_db),
) -> list[User]:
    users = db.exec(select(User)).all()
    return users


@router.post("/", dependencies=[Depends(is_miapeer_admin)], response_model=UserRead)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    db_user = User.from_orm(user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", dependencies=[Depends(is_miapeer_admin)], response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", dependencies=[Depends(is_miapeer_super_user)])
def delete_user(user_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.patch("/{user_id}", dependencies=[Depends(is_miapeer_super_user)], response_model=UserRead)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
) -> User:
    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.dict(exclude_unset=True)

    for key, value in user_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
