from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": now + expires_delta,
    }
    return cast(
        str,
        jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        ),
    )


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TOKEN_TYPE_ACCESS,
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TOKEN_TYPE_REFRESH,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return cast(dict[str, Any], payload)


__all__ = [
    "JWTError",
    "TOKEN_TYPE_ACCESS",
    "TOKEN_TYPE_REFRESH",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
]
