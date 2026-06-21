from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from tokyo.packages.contracts.api import ApiError
from tokyo.packages.contracts.base import TokyoBaseModel, normalize_utc


class WebSocketEnvelope(TokyoBaseModel):
    type: str = Field(min_length=1, max_length=128)
    version: int = Field(default=1, ge=1)
    request_id: UUID | None = None
    correlation_id: UUID = Field(default_factory=uuid4)
    sequence: int = Field(ge=0)
    timestamp: datetime
    source: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class SubscribePayload(TokyoBaseModel):
    channels: list[str] = Field(min_length=1)
    last_seen_sequence: dict[str, int] = Field(default_factory=dict)


class SubscriptionAckPayload(TokyoBaseModel):
    channels: list[str]


class SubscriptionRejectPayload(TokyoBaseModel):
    channels: list[str]
    error: ApiError


class HeartbeatPayload(TokyoBaseModel):
    sent_at: datetime

    @field_validator("sent_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

