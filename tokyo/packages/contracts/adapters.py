from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from tokyo.packages.contracts.base import TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import AdapterState


class AdapterHealth(TokyoBaseModel):
    adapter_id: str
    adapter_type: str
    state: AdapterState
    message: str = ""
    checked_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("checked_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class AdapterCapabilities(TokyoBaseModel):
    adapter_id: str
    adapter_type: str
    version: str
    provider: str
    supports_live: bool = False
    supports_backfill: bool = False
    supports_ticks: bool = False
    supports_bars: bool = False
    supports_order_book: bool = False
    supports_bid_ask: bool = False
    supports_market_orders: bool = False
    supports_limit_orders: bool = False
    supports_replace_order: bool = False
    supports_streaming_executions: bool = False
    symbols: list[dict[str, Any]] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

