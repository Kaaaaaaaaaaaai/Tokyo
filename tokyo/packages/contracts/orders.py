from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel, normalize_utc
from tokyo.packages.contracts.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
    TradingMode,
)


class OrderIntent(TokyoBaseModel):
    strategy_id: str = Field(min_length=1, max_length=96)
    account_id: str = Field(min_length=1, max_length=64)
    trading_mode: TradingMode = TradingMode.paper
    symbol_id: str = Field(min_length=8, max_length=32)
    side: OrderSide
    order_type: OrderType
    quantity: DecimalString
    limit_price: DecimalString | None = None
    stop_price: DecimalString | None = None
    time_in_force: TimeInForce = TimeInForce.day
    client_order_id: str = Field(min_length=1, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_type_prices(self) -> "OrderIntent":
        if self.order_type == OrderType.limit and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.order_type == OrderType.market and self.limit_price is not None:
            raise ValueError("limit_price is not accepted for market orders")
        return self


class Order(TokyoBaseModel):
    order_id: UUID = Field(default_factory=uuid4)
    client_order_id: str
    strategy_id: str
    account_id: str
    trading_mode: TradingMode
    symbol_id: str
    side: OrderSide
    order_type: OrderType
    quantity: DecimalString
    filled_quantity: DecimalString = "0"
    limit_price: DecimalString | None = None
    stop_price: DecimalString | None = None
    time_in_force: TimeInForce
    status: OrderStatus = OrderStatus.received
    adapter_id: str | None = None
    broker_order_id: str | None = None
    correlation_id: UUID = Field(default_factory=uuid4)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @classmethod
    def from_intent(cls, intent: OrderIntent, created_at: datetime, correlation_id: UUID) -> "Order":
        return cls(
            client_order_id=intent.client_order_id,
            strategy_id=intent.strategy_id,
            account_id=intent.account_id,
            trading_mode=intent.trading_mode,
            symbol_id=intent.symbol_id,
            side=intent.side,
            order_type=intent.order_type,
            quantity=intent.quantity,
            limit_price=intent.limit_price,
            stop_price=intent.stop_price,
            time_in_force=intent.time_in_force,
            correlation_id=correlation_id,
            metadata=dict(intent.metadata),
            created_at=created_at,
            updated_at=created_at,
        )


class OrderEvent(TokyoBaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    event_type: str = Field(min_length=1, max_length=64)
    previous_status: OrderStatus | None = None
    new_status: OrderStatus
    reason_code: str | None = None
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return normalize_utc(value)


class OrderDetail(TokyoBaseModel):
    order: Order
    events: list[OrderEvent]

