from datetime import UTC
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    utcnow,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import refresh_token_repository as refresh_token_repo
from app.repositories import user_repository as user_repo
from app.schemas.auth import RegisterRequest, TokenResponse


def _token_response(db: Session, user: User) -> TokenResponse:
    settings = get_settings()
    subject = str(user.id)
    access_token, access_expires_at = create_access_token(subject)
    refresh_jti = str(uuid4())
    refresh_token, refresh_expires_at = create_refresh_token(
        subject,
        jti=refresh_jti,
        token_version=user.token_version,
    )
    refresh_token_repo.create_refresh_token(
        db,
        user_id=user.id,
        jti=refresh_jti,
        expires_at=refresh_expires_at,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expires_in=int((access_expires_at - utcnow()).total_seconds()),
        refresh_token_expires_in=int(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def _invalid_refresh_token_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_refresh_token(refresh_token: str) -> tuple[int, str, int]:
    try:
        payload = decode_token(refresh_token)
        subject = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        token_version = payload.get("token_version")
        if (
            subject is None
            or token_type != TOKEN_TYPE_REFRESH
            or not isinstance(jti, str)
            or not isinstance(token_version, int)
        ):
            raise _invalid_refresh_token_exception()
        return int(str(subject)), jti, token_version
    except (JWTError, ValueError, TypeError) as exc:
        raise _invalid_refresh_token_exception() from exc


def _is_refresh_token_active(token: RefreshToken) -> bool:
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return token.revoked_at is None and expires_at > utcnow()


def register_user_service(db: Session, data: RegisterRequest) -> User:
    settings = get_settings()
    if not settings.ALLOW_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Open registration is disabled",
        )

    normalized_email = data.email.lower()
    existing = user_repo.get_user_by_email(db, normalized_email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    role = "user"
    if settings.AUTO_PROMOTE_FIRST_USER_TO_ADMIN and user_repo.count_users(db) == 0:
        role = "admin"

    try:
        user = user_repo.create_user(
            db,
            full_name=data.full_name,
            email=normalized_email,
            hashed_password=hash_password(data.password),
            role=role,
            is_active=True,
        )
        db.commit()
        return user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc


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
    tokens = _token_response(db, user)
    db.commit()
    return tokens


def refresh_token_service(db: Session, refresh_token: str) -> TokenResponse:
    user_id, current_jti, token_version = _decode_refresh_token(refresh_token)

    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise _invalid_refresh_token_exception()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    if user.token_version != token_version:
        refresh_token_repo.revoke_all_user_refresh_tokens(
            db,
            user_id=user.id,
            revoked_at=utcnow(),
        )
        db.commit()
        raise _invalid_refresh_token_exception()

    stored_token = refresh_token_repo.get_refresh_token_by_jti(db, current_jti)
    if stored_token is None or stored_token.user_id != user.id:
        raise _invalid_refresh_token_exception()
    if not _is_refresh_token_active(stored_token):
        refresh_token_repo.revoke_all_user_refresh_tokens(
            db,
            user_id=user.id,
            revoked_at=utcnow(),
        )
        db.commit()
        raise _invalid_refresh_token_exception()

    new_tokens = _token_response(db, user)
    replacement_jti = _decode_refresh_token(new_tokens.refresh_token)[1]
    refresh_token_repo.revoke_refresh_token(
        db,
        stored_token,
        revoked_at=utcnow(),
        replaced_by_jti=replacement_jti,
    )
    db.commit()
    return new_tokens


def logout_user_service(db: Session, refresh_token: str) -> None:
    try:
        _, current_jti, _ = _decode_refresh_token(refresh_token)
    except HTTPException:
        return

    stored_token = refresh_token_repo.get_refresh_token_by_jti(db, current_jti)
    if stored_token is None or stored_token.revoked_at is not None:
        return

    refresh_token_repo.revoke_refresh_token(
        db,
        stored_token,
        revoked_at=utcnow(),
    )
    db.commit()


def change_password_service(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    user_repo.update_user(
        db,
        user,
        hashed_password=hash_password(new_password),
        token_version=user.token_version + 1,
    )
    refresh_token_repo.revoke_all_user_refresh_tokens(
        db,
        user_id=user.id,
        revoked_at=utcnow(),
    )
    db.commit()
