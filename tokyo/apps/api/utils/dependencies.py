from secrets import compare_digest

from fastapi import Header, Request

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.common.errors import TokyoError, ValidationFailure
from tokyo.packages.contracts.enums import ErrorCode


def get_runtime(request: Request) -> TokyoRuntime:
    return request.app.state.runtime


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return None
    return value


def validate_api_key(
    settings: RuntimeSettings,
    x_api_key: str | None,
    authorization: str | None,
) -> None:
    if not settings.api_auth_required:
        return
    if not settings.api_key:
        raise TokyoError(
            ErrorCode.unauthorized,
            "Protected API routes require TOKYO_API_KEY to be configured.",
            {"env": "TOKYO_API_KEY"},
        )
    supplied_key = x_api_key or _bearer_token(authorization)
    if not supplied_key or not compare_digest(supplied_key, settings.api_key):
        raise TokyoError(
            ErrorCode.unauthorized,
            "Valid API key required.",
            {"headers": ["X-API-Key", "Authorization: Bearer <token>"]},
        )


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    validate_api_key(get_runtime(request).settings, x_api_key, authorization)


async def require_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    if not idempotency_key:
        raise ValidationFailure(
            ErrorCode.validation_error,
            "Mutating endpoint requires Idempotency-Key header.",
            {"header": "Idempotency-Key"},
        )
    return idempotency_key
