import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from tokyo.packages.contracts.account import Account
from tokyo.packages.contracts.enums import KillSwitchState, TradingMode
from tokyo.packages.contracts.risk import RiskLimit
from tokyo.packages.contracts.strategy import Strategy
from tokyo.packages.contracts.symbol import Symbol


class TokyoEnvironment(StrEnum):
    dev = "dev"
    paper = "paper"


class EventBusBackend(StrEnum):
    memory = "memory"
    redis = "redis"


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tokyo_env: TokyoEnvironment = Field(default=TokyoEnvironment.dev, alias="TOKYO_ENV")
    trading_mode: TradingMode = Field(default=TradingMode.paper, alias="TRADING_MODE")
    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    event_bus_backend: EventBusBackend = Field(
        default=EventBusBackend.memory, alias="EVENT_BUS_BACKEND"
    )
    redis_stream_max_len: int = Field(default=50_000, ge=1, alias="REDIS_STREAM_MAX_LEN")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    api_auth_required: bool = Field(default=True, alias="API_AUTH_REQUIRED")
    api_key: str | None = Field(default=None, alias="TOKYO_API_KEY")
    kill_switch_default: KillSwitchState = Field(
        default=KillSwitchState.engaged, alias="KILL_SWITCH_DEFAULT"
    )
    config_path: Path = Field(default=Path("config"), alias="CONFIG_PATH")
    secrets_provider: str = Field(default="env", alias="SECRETS_PROVIDER")
    webhook_alert_url: str | None = Field(default=None, alias="WEBHOOK_ALERT_URL")
    webhook_alert_kind: str | None = Field(default=None, alias="WEBHOOK_ALERT_KIND")

    @field_validator("trading_mode")
    @classmethod
    def reject_live_mode(cls, value: TradingMode) -> TradingMode:
        if value != TradingMode.paper:
            msg = "Tokyo MVP only supports TRADING_MODE=paper."
            raise ValueError(msg)
        return value

    @classmethod
    def from_environment(cls) -> "RuntimeSettings":
        return cls.model_validate(dict(os.environ))


class ConfigBundle(BaseModel):
    symbols: list[Symbol]
    accounts: list[Account]
    strategies: list[Strategy]
    risk_limits: list[RiskLimit]
    alerting: dict[str, Any]


class ConfigLoader:
    def __init__(self, root: Path) -> None:
        self._root = root

    def load(self) -> ConfigBundle:
        return ConfigBundle(
            symbols=[
                Symbol.model_validate(item) for item in self._read_list("symbols.yaml")
            ],
            accounts=[
                Account.model_validate(item) for item in self._read_list("accounts.yaml")
            ],
            strategies=[
                Strategy.model_validate(item) for item in self._read_list("strategies.yaml")
            ],
            risk_limits=[
                RiskLimit.model_validate(item) for item in self._read_list("risk_limits.yaml")
            ],
            alerting=self._read_dict("alerting.yaml"),
        )

    def _read_list(self, name: str) -> list[dict[str, Any]]:
        value = self._read_yaml(name)
        if not isinstance(value, list):
            msg = f"{name} must contain a YAML list."
            raise ValueError(msg)
        return value

    def _read_dict(self, name: str) -> dict[str, Any]:
        value = self._read_yaml(name)
        if not isinstance(value, dict):
            msg = f"{name} must contain a YAML mapping."
            raise ValueError(msg)
        return value

    def _read_yaml(self, name: str) -> Any:
        path = self._root / name
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
