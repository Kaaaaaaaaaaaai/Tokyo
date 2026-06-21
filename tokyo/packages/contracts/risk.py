from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import KillSwitchState, RiskSeverity


class RiskLimit(TokyoBaseModel):
    limit_id: str = Field(min_length=1, max_length=96)
    scope: str = Field(min_length=1, max_length=32)
    scope_id: str | None = None
    limit_type: str = Field(min_length=1, max_length=64)
    threshold: DecimalString
    action: str = Field(default="reject", min_length=1, max_length=64)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskEvent(TokyoBaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    severity: RiskSeverity
    event_type: str = Field(min_length=1, max_length=64)
    scope: str = Field(min_length=1, max_length=32)
    scope_id: str | None = None
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID = Field(default_factory=uuid4)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class RiskStatus(TokyoBaseModel):
    kill_switch_state: KillSwitchState
    active_limits: list[RiskLimit]
    risk_events: list[RiskEvent] = Field(default_factory=list)
    correlation_id: UUID = Field(default_factory=uuid4)

