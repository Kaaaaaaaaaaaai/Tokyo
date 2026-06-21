from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from tokyo.packages.contracts.base import TokyoBaseModel
from tokyo.packages.contracts.enums import ErrorCode


class ApiError(TokyoBaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID = Field(default_factory=uuid4)


class ApiErrorEnvelope(TokyoBaseModel):
    error: ApiError


class HealthResponse(TokyoBaseModel):
    status: str
    service: str
    dependencies: dict[str, str]
    correlation_id: UUID = Field(default_factory=uuid4)


class MutationResponse(TokyoBaseModel):
    status: str
    correlation_id: UUID = Field(default_factory=uuid4)

