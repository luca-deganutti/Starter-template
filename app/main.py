from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.bootstrap import bootstrap_initial_admin
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging, install_request_logging_middleware
from app.core.observability import configure_observability

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    bootstrap_initial_admin()
    yield


def create_app() -> FastAPI:
    configure_logging(settings.LOG_LEVEL, settings.DEBUG)
    application = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url=settings.DOCS_URL if settings.DOCS_ENABLED else None,
        redoc_url=settings.REDOC_URL if settings.DOCS_ENABLED else None,
        openapi_url=settings.OPENAPI_URL if settings.DOCS_ENABLED else None,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_logging_middleware(application)
    install_exception_handlers(application)
    configure_observability(application, settings)
    application.include_router(v1_router, prefix=settings.API_V1_PREFIX)
    return application


app = create_app()
