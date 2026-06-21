from typing import Any

from pydantic import Field

from tokyo.packages.contracts.base import DecimalString, TokyoBaseModel
from tokyo.packages.contracts.enums import TradingMode, Universe


class Account(TokyoBaseModel):
    account_id: str = Field(min_length=1, max_length=64)
    trading_mode: TradingMode = TradingMode.paper
    base_currency: str = Field(min_length=1, max_length=16)
    enabled: bool = True
    allowed_universes: list[Universe] = Field(default_factory=list)
    initial_balances: dict[str, DecimalString] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

