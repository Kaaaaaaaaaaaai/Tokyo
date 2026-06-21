from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import SymbolStatus, Universe, Variant


class Symbol(TokyoBaseModel):
    symbol_id: str = Field(min_length=8, max_length=32)
    symbol_uid: UUID = Field(default_factory=uuid4)
    symbol: str = Field(min_length=1, max_length=64)
    universe: Universe
    variant: Variant
    asset: str = Field(min_length=1, max_length=32)
    quote_asset: str | None = Field(default=None, max_length=32)
    unit: str = Field(min_length=1, max_length=32)
    price_precision: int = Field(ge=0, le=18)
    quantity_precision: int = Field(ge=0, le=18)
    min_quantity: DecimalString | None = None
    min_notional: DecimalString | None = None
    tick_size: DecimalString | None = None
    lot_size: DecimalString | None = None
    status: SymbolStatus = SymbolStatus.active
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("valid_from", "valid_to")
    @classmethod
    def ensure_utc(cls, value: datetime | None) -> datetime | None:
        return normalize_utc(value) if value else None


class ProviderSymbolMapping(TokyoBaseModel):
    provider_id: str = Field(min_length=1, max_length=64)
    provider_symbol: str = Field(min_length=1, max_length=128)
    symbol_id: str = Field(min_length=8, max_length=32)
    feed_type: str = Field(min_length=1, max_length=32)
    timezone: str = "UTC"
    is_tradeable: bool = False
    is_primary: bool = False
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("valid_from", "valid_to")
    @classmethod
    def ensure_utc(cls, value: datetime | None) -> datetime | None:
        return normalize_utc(value) if value else None

