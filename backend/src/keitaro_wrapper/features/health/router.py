from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from keitaro_wrapper.core.dependencies import KeitaroDep, SessionDep
from keitaro_wrapper.core.errors import AppError

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(
    session: SessionDep,
    keitaro: KeitaroDep,
) -> JSONResponse:
    checks: dict[str, Any] = {"database": "ok", "keitaro": "ok"}
    healthy = True

    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
        healthy = False

    try:
        await keitaro.ping()
    except AppError as exc:
        checks["keitaro"] = exc.message
        healthy = False
    except Exception as exc:  # pragma: no cover - defensive
        checks["keitaro"] = f"error: {type(exc).__name__}"
        healthy = False

    body = {"status": "ok" if healthy else "error", "checks": checks}
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body,
    )
