from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import OrderSide, TradingMode


class ExecutionReport(TokyoBaseModel):
    execution_id: UUID = Field(default_factory=uuid4)
    broker_execution_id: str | None = None
    order_id: UUID
    account_id: str
    strategy_id: str
    symbol_id: str
    trading_mode: TradingMode = TradingMode.paper
    side: OrderSide
    quantity: DecimalString
    price: DecimalString
    commission: DecimalString | None = None
    commission_asset: str | None = None
    liquidity: str | None = None
    executed_at: datetime
    received_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("executed_at", "received_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class Position(TokyoBaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    account_id: str
    strategy_id: str | None = None
    symbol_id: str
    trading_mode: TradingMode
    quantity: DecimalString
    average_entry_price: DecimalString | None = None
    mark_price: DecimalString | None = None
    realized_pnl: DecimalString = "0"
    unrealized_pnl: DecimalString = "0"
    source: str = "platform"
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class Balance(TokyoBaseModel):
    balance_id: UUID = Field(default_factory=uuid4)
    account_id: str
    asset: str
    available: DecimalString
    locked: DecimalString = "0"
    total: DecimalString
    source: str = "platform"
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

