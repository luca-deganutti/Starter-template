from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service as user_serv

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> User:
    return user_serv.create_user_service(db, data)


@router.get("", response_model=list[UserRead])
def get_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[User]:
    return user_serv.get_users_service(db, skip, limit)


@router.get("/by-email", response_model=UserRead)
def get_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> User:
    return user_serv.get_user_by_email_service(db, email)


@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> User:
    return user_serv.get_user_by_id_service(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> User:
    return user_serv.update_user_service(db, user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> None:
    user_serv.delete_user_service(db, user_id)
