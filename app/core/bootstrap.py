import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.repositories import user_repository as user_repo

logger = logging.getLogger("app.bootstrap")


def bootstrap_initial_admin() -> None:
    settings = get_settings()
    if settings.INITIAL_ADMIN_EMAIL is None or settings.INITIAL_ADMIN_PASSWORD is None:
        return

    db = SessionLocal()
    try:
        existing = user_repo.get_user_by_email(db, str(settings.INITIAL_ADMIN_EMAIL))
        if existing is not None:
            logger.info("initial admin already exists email=%s", existing.email)
            return

        user_repo.create_user(
            db,
            full_name=settings.INITIAL_ADMIN_FULL_NAME,
            email=str(settings.INITIAL_ADMIN_EMAIL),
            hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.commit()
        logger.info("initial admin created email=%s", settings.INITIAL_ADMIN_EMAIL)
    except IntegrityError:
        db.rollback()
        logger.info(
            "initial admin creation skipped because the user already exists email=%s",
            settings.INITIAL_ADMIN_EMAIL,
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception("failed to bootstrap initial admin")
    finally:
        db.close()
