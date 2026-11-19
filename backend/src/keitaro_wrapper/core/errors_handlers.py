from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from keitaro_wrapper.core.errors import AppError
from keitaro_wrapper.core.logging import get_logger

logger = get_logger(__name__)


def _payload(request: Request, exc: AppError) -> dict[str, Any]:
    body: dict[str, Any] = {
        "code": exc.code,
        "message": exc.message,
        "request_id": getattr(request.state, "request_id", None),
    }
    if exc.details:
        body["details"] = exc.details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_payload(request, exc))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while processing %s", request.url.path)
        error = AppError("Внутренняя ошибка сервиса", code="internal_error")
        if app.debug:
            error.details = {"type": type(exc).__name__, "message": str(exc)}
        return JSONResponse(status_code=500, content=_payload(request, error))
