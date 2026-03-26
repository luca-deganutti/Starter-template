from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, utcnow
from app.models.user import User
from app.repositories import refresh_token_repository as refresh_token_repo
from app.repositories import user_repository as user_repo
from app.schemas.user import UserCreate, UserUpdate


def _normalize_role(role: str) -> str:
    return role.strip().lower()


def create_user_service(db: Session, data: UserCreate) -> User:
    normalized_email = data.email.lower()
    existing = user_repo.get_user_by_email(db, normalized_email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )
    try:
        user = user_repo.create_user(
            db,
            full_name=data.full_name,
            email=normalized_email,
            hashed_password=hash_password(data.password),
            role=_normalize_role(data.role),
            is_active=data.is_active,
        )
        db.commit()
        return user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc


def update_user_service(db: Session, user_id: int, data: UserUpdate) -> User:
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if data.email is not None:
        existing = user_repo.get_user_by_email(db, data.email.lower())
        if existing is not None and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    hashed_password = None
    if data.password is not None:
        hashed_password = hash_password(data.password)

    normalized_role = None
    if data.role is not None:
        normalized_role = _normalize_role(data.role)

    try:
        updated_user = user_repo.update_user(
            db,
            user,
            full_name=data.full_name,
            email=data.email.lower() if data.email is not None else None,
            hashed_password=hashed_password,
            role=normalized_role,
            is_active=data.is_active,
            token_version=(
                user.token_version + 1 if hashed_password is not None else None
            ),
        )
        if hashed_password is not None or data.is_active is False:
            refresh_token_repo.revoke_all_user_refresh_tokens(
                db,
                user_id=user.id,
                revoked_at=utcnow(),
            )
        db.commit()
        return updated_user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc


def delete_user_service(db: Session, user_id: int) -> None:
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user_repo.delete_user(db, user)
    db.commit()


def get_user_by_id_service(db: Session, user_id: int) -> User:
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_users_service(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return user_repo.get_users(db, skip, limit)


def get_user_by_email_service(db: Session, email: str) -> User:
    user = user_repo.get_user_by_email(db, email.lower())
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
