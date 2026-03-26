from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.auth_router import router as auth_router
from app.api.v1.user_router import router as user_router
from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()
router = APIRouter()


@router.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENV,
    }


@router.get("/ready", tags=["health"])
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from exc
    return {"status": "ok", "database": "ready"}


router.include_router(auth_router)
router.include_router(user_router)
