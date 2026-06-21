from typing import Any

from pydantic import Field

from tokyo.packages.contracts.base import TokyoBaseModel


class Strategy(TokyoBaseModel):
    strategy_id: str = Field(min_length=1, max_length=96)
    enabled: bool = True
    allowed_accounts: list[str] = Field(default_factory=list)
    allowed_symbols: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

