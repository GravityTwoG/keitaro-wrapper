from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class AppError(Exception):
    """Base error that is translated to a JSON response by the API layer."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class KeitaroApiError(AppError):
    """Keitaro rejected the request or is unreachable."""

    status_code = 502
    code = "keitaro_error"


class KeitaroUnavailableError(KeitaroApiError):
    status_code = 503
    code = "keitaro_unavailable"
