from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    *,
    jti: str | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti
    if additional_claims is not None:
        payload.update(additional_claims)
    return (
        jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        ),
        expires_at,
    )


def create_access_token(subject: str) -> tuple[str, datetime]:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TOKEN_TYPE_ACCESS,
    )


def create_refresh_token(
    subject: str,
    *,
    jti: str,
    token_version: int,
) -> tuple[str, datetime]:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TOKEN_TYPE_REFRESH,
        jti=jti,
        additional_claims={"token_version": token_version},
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload


def utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "JWTError",
    "TOKEN_TYPE_ACCESS",
    "TOKEN_TYPE_REFRESH",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "utcnow",
    "verify_password",
]
