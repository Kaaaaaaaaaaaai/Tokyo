from datetime import date
from typing import Any

from pydantic import Field

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel
from tokyo.packages.contracts.enums import TradingMode


class DailyReport(TokyoBaseModel):
    date: date
    trading_mode: TradingMode
    account_id: str | None = None
    strategy_id: str | None = None
    starting_balance: DecimalString = "0"
    ending_balance: DecimalString = "0"
    realized_pnl: DecimalString = "0"
    unrealized_pnl: DecimalString = "0"
    gross_exposure: DecimalString = "0"
    net_exposure: DecimalString = "0"
    order_intents: int = 0
    accepted_orders: int = 0
    rejected_orders: int = 0
    fills: int = 0
    cancel_requests: int = 0
    cancel_failures: int = 0
    largest_position: dict[str, Any] | None = None
    largest_loss_event: dict[str, Any] | None = None
    risk_alerts: int = 0
    data_gaps: int = 0
    adapter_incidents: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

