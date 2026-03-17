from fastapi import APIRouter

from app.api.v1.auth_router import router as auth_router
from app.core.config import get_settings
from app.api.v1.user_router import router as user_router

settings = get_settings()
router = APIRouter()


@router.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENV,
    }


router.include_router(auth_router)
router.include_router(user_router)
