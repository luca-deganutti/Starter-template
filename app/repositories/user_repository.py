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
    db.flush()
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
    token_version: int | None = None,
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
    if token_version is not None:
        user.token_version = token_version

    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return cast(User | None, db.scalar(stmt))


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower())
    return cast(User | None, db.scalar(stmt))


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    stmt = select(User).order_by(User.id.asc()).offset(skip).limit(limit)
    return cast(list[User], list(db.scalars(stmt).all()))


def count_users(db: Session) -> int:
    stmt = select(func.count(User.id))
    return int(db.scalar(stmt) or 0)
