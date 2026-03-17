from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    JWTError,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import user_repository as user_repo
from app.schemas.auth import RegisterRequest, TokenResponse


def _token_response(user: User) -> TokenResponse:
    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def register_user_service(db: Session, data: RegisterRequest) -> User:
    normalized_email = data.email.lower()
    existing = user_repo.get_user_by_email(db, normalized_email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    role = "admin" if user_repo.count_users(db) == 0 else "user"
    return user_repo.create_user(
        db,
        full_name=data.full_name,
        email=normalized_email,
        hashed_password=hash_password(data.password),
        role=role,
        is_active=True,
    )


def authenticate_user_service(db: Session, email: str, password: str) -> User:
    user = user_repo.get_user_by_email(db, email.lower())
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


def login_user_service(db: Session, email: str, password: str) -> TokenResponse:
    user = authenticate_user_service(db, email, password)
    return _token_response(user)


def refresh_token_service(db: Session, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
        subject = payload.get("sub")
        token_type = payload.get("type")
        if subject is None or token_type != TOKEN_TYPE_REFRESH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(str(subject))
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return _token_response(user)
