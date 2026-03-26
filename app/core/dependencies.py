from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TOKEN_TYPE_ACCESS, JWTError, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories import user_repository as user_repo

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        token_type = payload.get("type")
        if subject is None or token_type != TOKEN_TYPE_ACCESS:
            raise _credentials_exception()
        user_id = int(str(subject))
    except (JWTError, ValueError) as exc:
        raise _credentials_exception() from exc

    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise _credentials_exception()
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    normalized_roles = {role.strip().lower() for role in allowed_roles}

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.strip().lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return current_user

    return dependency


def get_current_admin_user(
    current_user: User = Depends(require_roles("admin")),
) -> User:
    return current_user
