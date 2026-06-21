from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from tokyo.packages.common.errors import ConflictError, NotFoundError, TokyoError
from tokyo.packages.contracts.api import ApiError, ApiErrorEnvelope
from tokyo.packages.contracts.enums import ErrorCode


def status_code_for(error: TokyoError) -> int:
    if isinstance(error, NotFoundError):
        return 404
    if isinstance(error, ConflictError):
        return 409
    if error.code == ErrorCode.unauthorized:
        return 401
    if error.code == ErrorCode.forbidden:
        return 403
    if error.code == ErrorCode.validation_error:
        return 422
    return 400


async def tokyo_error_handler(request: Request, error: TokyoError) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(
            code=error.code,
            message=error.message,
            details=error.details,
            correlation_id=error.correlation_id,
        )
    )
    return JSONResponse(
        status_code=status_code_for(error),
        content=envelope.model_dump(mode="json"),
    )


async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(
            code=ErrorCode.validation_error,
            message="Request validation failed.",
            details={"errors": error.errors()},
        )
    )
    return JSONResponse(status_code=422, content=envelope.model_dump(mode="json"))
