from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def install_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(
                detail=exc.detail,
                request_id=_get_request_id(request),
            ),
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_build_error_payload(
                detail="Validation error",
                request_id=_get_request_id(request),
                errors=exc.errors(),
            ),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        _: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_payload(
                detail="Internal server error",
                request_id=_get_request_id(request),
            ),
        )


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _build_error_payload(
    *,
    detail: Any,
    request_id: str,
    errors: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": detail,
        "request_id": request_id,
    }
    if errors is not None:
        payload["errors"] = list(errors)
    return payload
