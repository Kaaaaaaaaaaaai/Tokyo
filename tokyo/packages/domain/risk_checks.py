from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from tokyo.packages.common.errors import ValidationFailure
from tokyo.packages.contracts.account import Account
from tokyo.packages.contracts.enums import (
    ErrorCode,
    KillSwitchState,
    OrderType,
    SymbolStatus,
    TimeInForce,
    TradingMode,
    Universe,
)
from tokyo.packages.contracts.orders import OrderIntent
from tokyo.packages.contracts.risk import RiskLimit
from tokyo.packages.contracts.strategy import Strategy
from tokyo.packages.contracts.symbol import Symbol
from tokyo.packages.domain.decimals import DecimalRules


@dataclass(frozen=True, slots=True)
class LatestPrice:
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    close: Decimal | None
    source_timestamp: datetime
    received_at: datetime

    def reference_price(self, side: str) -> Decimal | None:
        if side == "buy":
            return self.ask or self.last or self.close or self.bid
        return self.bid or self.last or self.close or self.ask


@dataclass(frozen=True, slots=True)
class RiskValidationContext:
    strategy: Strategy | None
    account: Account | None
    symbol: Symbol | None
    kill_switch_state: KillSwitchState
    latest_price: LatestPrice | None
    risk_limits: list[RiskLimit]
    now: datetime
    paper_adapter_healthy: bool = True
    correlation_id: UUID = uuid4()


class RiskEngine:
    """Fail-closed MVP validation pipeline for paper order intents."""

    supported_order_types = {OrderType.market, OrderType.limit}
    supported_time_in_force = {TimeInForce.day, TimeInForce.gtc}

    def validate(self, intent: OrderIntent, context: RiskValidationContext) -> None:
        correlation_id = context.correlation_id
        if context.strategy is None:
            raise ValidationFailure(
                ErrorCode.not_found,
                "Strategy does not exist.",
                {"strategy_id": intent.strategy_id},
                correlation_id,
            )
        if not context.strategy.enabled:
            raise ValidationFailure(
                ErrorCode.strategy_disabled,
                "Strategy is disabled.",
                {"strategy_id": intent.strategy_id},
                correlation_id,
            )
        if context.account is None:
            raise ValidationFailure(
                ErrorCode.not_found,
                "Account does not exist.",
                {"account_id": intent.account_id},
                correlation_id,
            )
        if not context.account.enabled:
            raise ValidationFailure(
                ErrorCode.forbidden,
                "Account is disabled.",
                {"account_id": intent.account_id},
                correlation_id,
            )
        if intent.trading_mode != TradingMode.paper:
            raise ValidationFailure(
                ErrorCode.live_mode_unsupported,
                "Tokyo MVP rejects live order intents.",
                {"trading_mode": intent.trading_mode.value},
                correlation_id,
            )
        if context.account.trading_mode != intent.trading_mode:
            raise ValidationFailure(
                ErrorCode.forbidden,
                "Account trading mode does not match order intent.",
                {"account_mode": context.account.trading_mode.value},
                correlation_id,
            )
        if context.symbol is None:
            raise ValidationFailure(
                ErrorCode.not_found,
                "Symbol does not exist.",
                {"symbol_id": intent.symbol_id},
                correlation_id,
            )
        if context.symbol.status != SymbolStatus.active:
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Symbol is not active.",
                {"symbol_id": intent.symbol_id, "status": context.symbol.status.value},
                correlation_id,
            )
        if context.symbol.universe not in {Universe.fx, Universe.crypto}:
            raise ValidationFailure(
                ErrorCode.validation_error,
                "MVP supports only FX and crypto instruments.",
                {"universe": context.symbol.universe.value},
                correlation_id,
            )
        if (
            context.account.allowed_universes
            and context.symbol.universe not in context.account.allowed_universes
        ):
            raise ValidationFailure(
                ErrorCode.forbidden,
                "Account is not permitted for symbol universe.",
                {"universe": context.symbol.universe.value},
                correlation_id,
            )
        if intent.order_type not in self.supported_order_types:
            raise ValidationFailure(
                ErrorCode.order_type_unsupported,
                "Order type is not supported in MVP.",
                {"order_type": intent.order_type.value},
                correlation_id,
            )
        if intent.time_in_force not in self.supported_time_in_force:
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Time in force is not supported in MVP.",
                {"time_in_force": intent.time_in_force.value},
                correlation_id,
            )
        if context.kill_switch_state != KillSwitchState.released:
            raise ValidationFailure(
                ErrorCode.kill_switch_engaged,
                "Kill switch is engaged.",
                {"kill_switch_state": context.kill_switch_state.value},
                correlation_id,
            )
        if not context.paper_adapter_healthy:
            raise ValidationFailure(
                ErrorCode.adapter_unavailable,
                "Paper market adapter is unavailable.",
                {"adapter_id": "paper_sim"},
                correlation_id,
            )

        quantity = intent.quantity
        if not DecimalRules.is_positive(quantity):
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Order quantity must be positive.",
                {"quantity": str(quantity)},
                correlation_id,
            )
        if not DecimalRules.is_multiple(quantity, context.symbol.lot_size):
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Order quantity does not respect lot size.",
                {"quantity": str(quantity), "lot_size": str(context.symbol.lot_size)},
                correlation_id,
            )
        if context.symbol.min_quantity is not None and quantity < context.symbol.min_quantity:
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Order quantity is below minimum quantity.",
                {"min_quantity": str(context.symbol.min_quantity)},
                correlation_id,
            )
        if intent.limit_price is not None and not DecimalRules.is_multiple(
            intent.limit_price, context.symbol.tick_size
        ):
            raise ValidationFailure(
                ErrorCode.validation_error,
                "Limit price does not respect tick size.",
                {"limit_price": str(intent.limit_price), "tick_size": str(context.symbol.tick_size)},
                correlation_id,
            )

        if context.latest_price is None:
            raise ValidationFailure(
                ErrorCode.market_data_stale,
                "No latest market data is available for the symbol.",
                {"symbol_id": intent.symbol_id},
                correlation_id,
            )
        price = intent.limit_price or context.latest_price.reference_price(intent.side.value)
        if price is None:
            raise ValidationFailure(
                ErrorCode.market_data_stale,
                "Latest market data has no usable price.",
                {"symbol_id": intent.symbol_id},
                correlation_id,
            )
        notional = DecimalRules.notional(quantity, price)
        if context.symbol.min_notional is not None and notional is not None:
            if notional < context.symbol.min_notional:
                raise ValidationFailure(
                    ErrorCode.validation_error,
                    "Order notional is below minimum notional.",
                    {"min_notional": str(context.symbol.min_notional), "notional": str(notional)},
                    correlation_id,
                )

        for risk_limit in context.risk_limits:
            if not risk_limit.enabled:
                continue
            self._check_limit(risk_limit, quantity, notional, context.symbol, correlation_id)

    def _check_limit(
        self,
        risk_limit: RiskLimit,
        quantity: Decimal,
        notional: Decimal | None,
        symbol: Symbol,
        correlation_id: UUID,
    ) -> None:
        if risk_limit.scope == "universe" and risk_limit.scope_id != symbol.universe.value:
            return
        if risk_limit.scope == "symbol" and risk_limit.scope_id != symbol.symbol_id:
            return
        if risk_limit.limit_type in {"max_fx_order_quantity", "max_order_quantity"}:
            if quantity > risk_limit.threshold:
                raise ValidationFailure(
                    ErrorCode.risk_limit_exceeded,
                    "Order quantity exceeds configured limit.",
                    {"limit_id": risk_limit.limit_id, "threshold": str(risk_limit.threshold)},
                    correlation_id,
                )
        if risk_limit.limit_type in {"max_order_notional", "max_crypto_order_notional"}:
            if notional is None or notional > risk_limit.threshold:
                raise ValidationFailure(
                    ErrorCode.risk_limit_exceeded,
                    "Order notional exceeds configured limit.",
                    {
                        "limit_id": risk_limit.limit_id,
                        "threshold": str(risk_limit.threshold),
                        "notional": str(notional) if notional is not None else None,
                    },
                    correlation_id,
                )

