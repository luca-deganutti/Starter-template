import logging
import logging.config
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint


def configure_logging(level: str, debug: bool) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s %(levelname)s %(name)s "
                        "[request_id=%(request_id)s] %(message)s"
                    ),
                },
            },
            "filters": {
                "request_context": {
                    "()": "app.core.logging.RequestContextFilter",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_context"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "DEBUG" if debug else level,
            },
        }
    )


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def install_request_logging_middleware(application: FastAPI) -> None:
    logger = logging.getLogger("app.request")

    @application.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        started = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started) * 1000
            logger.exception(
                "request failed method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                duration_ms,
                extra={"request_id": request_id},
            )
            raise

        duration_ms = (perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response
