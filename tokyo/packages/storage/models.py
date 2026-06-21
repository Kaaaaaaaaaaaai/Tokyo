from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uuid_column(primary_key: bool = False) -> Mapped[UUID]:
    return mapped_column(PostgresUUID(as_uuid=True), primary_key=primary_key)


class SymbolModel(Base):
    __tablename__ = "symbols"

    symbol_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    symbol_uid: Mapped[UUID] = uuid_column()
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    universe: Mapped[str] = mapped_column(String(32), nullable=False)
    variant: Mapped[str] = mapped_column(String(32), nullable=False)
    asset: Mapped[str] = mapped_column(String(32), nullable=False)
    quote_asset: Mapped[str | None] = mapped_column(String(32))
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    price_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    min_quantity: Mapped[Decimal | None] = mapped_column(Numeric)
    min_notional: Mapped[Decimal | None] = mapped_column(Numeric)
    tick_size: Mapped[Decimal | None] = mapped_column(Numeric)
    lot_size: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("symbol_uid", name="uq_symbols_symbol_uid"),)


class ProviderSymbolMappingModel(Base):
    __tablename__ = "provider_symbol_mappings"

    id: Mapped[UUID] = uuid_column(primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_symbol: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(32), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_tradeable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "provider_symbol",
            "feed_type",
            "valid_from",
            name="uq_provider_symbol_mapping_version",
        ),
    )


class StrategyModel(Base):
    __tablename__ = "strategies"

    strategy_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_accounts: Mapped[list[str]] = mapped_column(JSON, default=list)
    allowed_symbols: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AccountModel(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_universes: Mapped[list[str]] = mapped_column(JSON, default=list)
    initial_balances: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketTickModel(Base):
    __tablename__ = "market_ticks"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(128))
    source_sequence: Mapped[str | None] = mapped_column(String(128))
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bid: Mapped[Decimal | None] = mapped_column(Numeric)
    ask: Mapped[Decimal | None] = mapped_column(Numeric)
    last: Mapped[Decimal | None] = mapped_column(Numeric)
    volume: Mapped[Decimal | None] = mapped_column(Numeric)
    quality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (Index("ix_market_ticks_symbol_source_ts", "symbol_id", "source_timestamp"),)


class MarketBarModel(Base):
    __tablename__ = "market_bars"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    interval: Mapped[str] = mapped_column(String(16), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    volume: Mapped[Decimal | None] = mapped_column(Numeric)
    trade_count: Mapped[int | None] = mapped_column(Integer)
    vwap: Mapped[Decimal | None] = mapped_column(Numeric)
    quality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (Index("ix_market_bars_symbol_interval_opened", "symbol_id", "interval", "opened_at"),)


class DatasetRecordModel(Base):
    __tablename__ = "dataset_records"

    record_id: Mapped[UUID] = uuid_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    partition: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    symbol_id: Mapped[str | None] = mapped_column(String(32))
    provider_symbol: Mapped[str | None] = mapped_column(String(128))
    time_range: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    compression: Mapped[str | None] = mapped_column(String(32))
    encoding: Mapped[str | None] = mapped_column(String(32))
    content_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_ref: Mapped[str | None] = mapped_column(Text)
    payload_inline: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class BackfillJobModel(Base):
    __tablename__ = "backfill_jobs"

    job_id: Mapped[UUID] = uuid_column(primary_key=True)
    request: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rows_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gaps_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_backfill_jobs_status_created", "status", "created_at"),)


class OrderModel(Base):
    __tablename__ = "orders"

    order_id: Mapped[UUID] = uuid_column(primary_key=True)
    client_order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(96), nullable=False)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=Decimal("0"))
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric)
    time_in_force: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    adapter_id: Mapped[str | None] = mapped_column(String(64))
    broker_order_id: Mapped[str | None] = mapped_column(String(128))
    correlation_id: Mapped[UUID] = uuid_column()
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "strategy_id",
            "account_id",
            "trading_mode",
            "client_order_id",
            name="uq_orders_client_order_id",
        ),
        Index("ix_orders_strategy_created", "strategy_id", "created_at"),
        Index("ix_orders_account_created", "account_id", "created_at"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_client_order_id", "client_order_id"),
    )


class OrderEventModel(Base):
    __tablename__ = "order_events"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    order_id: Mapped[UUID] = uuid_column()
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[UUID] = uuid_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_order_events_order_created", "order_id", "created_at"),)


class ExecutionModel(Base):
    __tablename__ = "executions"

    execution_id: Mapped[UUID] = uuid_column(primary_key=True)
    broker_execution_id: Mapped[str | None] = mapped_column(String(128))
    order_id: Mapped[UUID] = uuid_column()
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(96), nullable=False)
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    commission: Mapped[Decimal | None] = mapped_column(Numeric)
    commission_asset: Mapped[str | None] = mapped_column(String(32))
    liquidity: Mapped[str | None] = mapped_column(String(32))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_executions_order_id", "order_id"),
        Index("ix_executions_account_executed", "account_id", "executed_at"),
    )


class PositionModel(Base):
    __tablename__ = "positions"

    position_id: Mapped[UUID] = uuid_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_id: Mapped[str | None] = mapped_column(String(96))
    symbol_id: Mapped[str] = mapped_column(String(32), nullable=False)
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    average_entry_price: Mapped[Decimal | None] = mapped_column(Numeric)
    mark_price: Mapped[Decimal | None] = mapped_column(Numeric)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=Decimal("0"))
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=Decimal("0"))
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_positions_account_symbol_asof", "account_id", "symbol_id", "as_of"),)


class BalanceModel(Base):
    __tablename__ = "balances"

    balance_id: Mapped[UUID] = uuid_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    asset: Mapped[str] = mapped_column(String(32), nullable=False)
    available: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    locked: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RiskLimitModel(Base):
    __tablename__ = "risk_limits"

    limit_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(String(96))
    limit_type: Mapped[str] = mapped_column(String(64), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RiskEventModel(Base):
    __tablename__ = "risk_events"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(String(96))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[UUID] = uuid_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_risk_events_severity_created", "severity", "created_at"),)


class AdapterEventModel(Base):
    __tablename__ = "adapter_events"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    adapter_id: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_adapter_events_adapter_created", "adapter_id", "created_at"),)


class SystemEventModel(Base):
    __tablename__ = "system_events"

    event_id: Mapped[UUID] = uuid_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[UUID] = uuid_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_system_events_created", "created_at"),)


class IdempotencyKeyModel(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[UUID] = uuid_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    route: Mapped[str] = mapped_column(String(256), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("key", "route", "actor_id", name="uq_idempotency_keys"),)

