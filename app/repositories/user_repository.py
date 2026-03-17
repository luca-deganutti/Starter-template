from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    hashed_password: str,
    role: str = "user",
    is_active: bool = True,
) -> User:
    user = User(
        full_name=full_name,
        email=email.lower(),
        hashed_password=hashed_password,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    full_name: str | None = None,
    email: str | None = None,
    hashed_password: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    if full_name is not None:
        user.full_name = full_name
    if email is not None:
        user.email = email.lower()
    if hashed_password is not None:
        user.hashed_password = hashed_password
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return cast(User | None, db.query(User).filter(User.id == user_id).first())


def get_user_by_email(db: Session, email: str) -> User | None:
    return cast(
        User | None,
        db.query(User).filter(User.email == email.lower()).first(),
    )


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return cast(list[User], db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all())


def count_users(db: Session) -> int:
    stmt = select(func.count()).select_from(User)
    return int(db.scalar(stmt) or 0)

