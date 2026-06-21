from enum import StrEnum


class Universe(StrEnum):
    fx = "fx"
    crypto = "crypto"
    stock = "stock"
    futures = "futures"


class Variant(StrEnum):
    spot = "spot"
    future = "future"
    perpetual = "perpetual"
    option = "option"


class SymbolStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class TradingMode(StrEnum):
    paper = "paper"
    live = "live"


class OrderSide(StrEnum):
    buy = "buy"
    sell = "sell"


class OrderType(StrEnum):
    market = "market"
    limit = "limit"
    stop = "stop"
    stop_limit = "stop_limit"


class TimeInForce(StrEnum):
    day = "day"
    gtc = "gtc"
    ioc = "ioc"
    fok = "fok"


class OrderStatus(StrEnum):
    received = "RECEIVED"
    validating = "VALIDATING"
    rejected = "REJECTED"
    accepted = "ACCEPTED"
    submitting = "SUBMITTING"
    submitted = "SUBMITTED"
    acknowledged = "ACKNOWLEDGED"
    partially_filled = "PARTIALLY_FILLED"
    filled = "FILLED"
    cancel_requested = "CANCEL_REQUESTED"
    canceled = "CANCELED"
    cancel_rejected = "CANCEL_REJECTED"
    expired = "EXPIRED"
    failed = "FAILED"
    unknown = "UNKNOWN"
    reconciled = "RECONCILED"


class ErrorCode(StrEnum):
    validation_error = "VALIDATION_ERROR"
    unauthorized = "UNAUTHORIZED"
    forbidden = "FORBIDDEN"
    not_found = "NOT_FOUND"
    conflict = "CONFLICT"
    kill_switch_engaged = "KILL_SWITCH_ENGAGED"
    strategy_disabled = "STRATEGY_DISABLED"
    risk_limit_exceeded = "RISK_LIMIT_EXCEEDED"
    market_data_stale = "MARKET_DATA_STALE"
    broker_unreconciled = "BROKER_UNRECONCILED"
    adapter_unavailable = "ADAPTER_UNAVAILABLE"
    broker_rejected = "BROKER_REJECTED"
    rate_limited = "RATE_LIMITED"
    internal_error = "INTERNAL_ERROR"
    live_mode_unsupported = "LIVE_MODE_UNSUPPORTED"
    order_type_unsupported = "ORDER_TYPE_UNSUPPORTED"
    client_order_id_conflict = "CLIENT_ORDER_ID_CONFLICT"
    order_not_open = "ORDER_NOT_OPEN"
    snapshot_required = "SNAPSHOT_REQUIRED"
    backpressure = "BACKPRESSURE"


class KillSwitchState(StrEnum):
    engaged = "engaged"
    released = "released"
    engaging = "engaging"


class RiskSeverity(StrEnum):
    info = "info"
    warning = "warning"
    critical = "critical"
    emergency = "emergency"


class AdapterState(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    disabled = "disabled"
    unavailable = "unavailable"


class BackfillStatus(StrEnum):
    requested = "requested"
    running = "running"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"

