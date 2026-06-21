from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from tokyo.packages.contracts.base import TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import RiskSeverity


class SystemEvent(TokyoBaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(min_length=1, max_length=64)
    actor_type: str = Field(min_length=1, max_length=32)
    actor_id: str | None = None
    severity: RiskSeverity = RiskSeverity.info
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID = Field(default_factory=uuid4)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

