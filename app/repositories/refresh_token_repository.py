from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create_refresh_token(
    db: Session,
    *,
    user_id: int,
    jti: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(token)
    db.flush()
    db.refresh(token)
    return token


def get_refresh_token_by_jti(db: Session, jti: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.jti == jti)
    return db.scalar(stmt)


def revoke_refresh_token(
    db: Session,
    token: RefreshToken,
    *,
    revoked_at: datetime,
    replaced_by_jti: str | None = None,
) -> RefreshToken:
    token.revoked_at = revoked_at
    token.replaced_by_jti = replaced_by_jti
    db.add(token)
    db.flush()
    db.refresh(token)
    return token


def revoke_all_user_refresh_tokens(
    db: Session,
    *,
    user_id: int,
    revoked_at: datetime,
) -> None:
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )
    db.execute(stmt)
