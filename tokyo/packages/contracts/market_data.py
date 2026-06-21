from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import BackfillStatus


class TickQuality(TokyoBaseModel):
    is_delayed: bool = False
    is_stale: bool = False
    is_duplicate: bool = False
    is_out_of_order: bool = False
    has_gap_before: bool = False
    repair_status: str = "raw"


class BarQuality(TokyoBaseModel):
    is_complete: bool = True
    has_gap: bool = False
    repair_status: str = "raw"


class DatasetQuality(TokyoBaseModel):
    is_duplicate: bool = False
    is_partial: bool = False
    checksum_valid: bool = True
    repair_status: str = "raw"


class TimeRange(TokyoBaseModel):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class MarketTick(TokyoBaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    symbol_id: str = Field(min_length=8, max_length=32)
    source: str = Field(min_length=1, max_length=64)
    source_event_id: str | None = None
    source_sequence: str | None = None
    source_timestamp: datetime
    ingested_at: datetime
    event_type: Literal["market.tick"] = "market.tick"
    bid: DecimalString | None = None
    ask: DecimalString | None = None
    last: DecimalString | None = None
    volume: DecimalString | None = None
    quality: TickQuality = Field(default_factory=TickQuality)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_timestamp", "ingested_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def require_price(self) -> "MarketTick":
        if self.bid is None and self.ask is None and self.last is None:
            raise ValueError("market tick requires at least one price field")
        return self


class MarketBar(TokyoBaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    symbol_id: str = Field(min_length=8, max_length=32)
    source: str = Field(min_length=1, max_length=64)
    interval: str = Field(min_length=1, max_length=16)
    opened_at: datetime
    closed_at: datetime
    event_type: Literal["market.bar"] = "market.bar"
    open: DecimalString
    high: DecimalString
    low: DecimalString
    close: DecimalString
    volume: DecimalString | None = None
    trade_count: int | None = Field(default=None, ge=0)
    vwap: DecimalString | None = None
    quality: BarQuality = Field(default_factory=BarQuality)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("opened_at", "closed_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def validate_time_range(self) -> "MarketBar":
        if self.closed_at <= self.opened_at:
            raise ValueError("closed_at must be after opened_at")
        return self


class DatasetRecord(TokyoBaseModel):
    record_id: UUID = Field(default_factory=uuid4)
    dataset_id: str = Field(min_length=1, max_length=128)
    dataset_type: str = Field(min_length=1, max_length=64)
    provider: str = Field(min_length=1, max_length=64)
    source_uri: str = Field(min_length=1)
    partition: dict[str, str] = Field(default_factory=dict)
    symbol_id: str | None = None
    provider_symbol: str | None = None
    time_range: TimeRange | None = None
    format: str = Field(min_length=1, max_length=32)
    compression: str | None = None
    encoding: str | None = None
    content_hash: str = Field(min_length=1, max_length=256)
    content_length: int = Field(ge=0)
    payload_ref: str | None = None
    payload_inline: str | None = None
    retrieved_at: datetime
    quality: DatasetQuality = Field(default_factory=DatasetQuality)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("retrieved_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class BackfillRequest(TokyoBaseModel):
    adapter_id: str = Field(min_length=1, max_length=64)
    symbol_ids: list[str] = Field(min_length=1)
    event_type: Literal["market.tick", "market.bar", "dataset"]
    start: datetime
    end: datetime
    interval: str | None = None
    repair_mode: bool = False

    @field_validator("start", "end")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def validate_range(self) -> "BackfillRequest":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        if self.event_type == "market.bar" and self.interval is None:
            raise ValueError("interval is required for bar backfills")
        return self


class BackfillJob(TokyoBaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    request: BackfillRequest
    status: BackfillStatus = BackfillStatus.requested
    rows_fetched: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    gaps_found: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("started_at", "finished_at")
    @classmethod
    def ensure_optional_utc(cls, value: datetime | None) -> datetime | None:
        return normalize_utc(value) if value else None

