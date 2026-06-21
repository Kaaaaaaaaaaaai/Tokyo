from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from tokyo.packages.adapters.market.base import MarketAdapter
from tokyo.packages.contracts.adapters import AdapterCapabilities, AdapterHealth
from tokyo.packages.contracts.enums import AdapterState, OrderSide, OrderType
from tokyo.packages.contracts.execution import Balance, ExecutionReport, Position
from tokyo.packages.contracts.orders import Order
from tokyo.packages.domain.risk_checks import LatestPrice


@dataclass(slots=True)
class PaperMarketConfig:
    slippage: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    partial_fills_enabled: bool = False
    rejection_simulation_enabled: bool = False


class PaperMarketAdapter(MarketAdapter):
    adapter_id = "paper_sim"
    adapter_type = "market"
    version = "0.1.0"

    def __init__(self, latest_prices: dict[str, LatestPrice], config: PaperMarketConfig | None = None) -> None:
        self._latest_prices = latest_prices
        self._config = config or PaperMarketConfig()
        self._running = True

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def health(self) -> AdapterHealth:
        return AdapterHealth(
            adapter_id=self.adapter_id,
            adapter_type=self.adapter_type,
            state=AdapterState.healthy if self._running else AdapterState.unavailable,
            checked_at=datetime.now(UTC),
        )

    async def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_id=self.adapter_id,
            adapter_type=self.adapter_type,
            version=self.version,
            provider="tokyo",
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_live=False,
        )

    async def submit_order(self, order: Order) -> ExecutionReport | None:
        latest = self._latest_prices.get(order.symbol_id)
        if latest is None:
            return None
        fill_price = self._fill_price(order, latest)
        if fill_price is None:
            return None
        now = datetime.now(UTC)
        return ExecutionReport(
            order_id=order.order_id,
            account_id=order.account_id,
            strategy_id=order.strategy_id,
            symbol_id=order.symbol_id,
            trading_mode=order.trading_mode,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=self._config.commission,
            commission_asset=None,
            executed_at=now,
            received_at=now,
            metadata={"adapter_id": self.adapter_id},
        )

    async def cancel_order(self, order: Order) -> None:
        return None

    async def fetch_positions(self) -> list[Position]:
        return []

    async def fetch_balances(self) -> list[Balance]:
        return []

    def _fill_price(self, order: Order, latest: LatestPrice) -> Decimal | None:
        reference = latest.reference_price(order.side.value)
        if reference is None:
            return None
        if order.order_type == OrderType.market:
            return self._apply_slippage(reference, order.side)
        if order.order_type == OrderType.limit:
            return self._limit_fill_price(order, latest)
        return None

    def _limit_fill_price(self, order: Order, latest: LatestPrice) -> Decimal | None:
        if order.limit_price is None:
            return None
        reference = latest.reference_price(order.side.value)
        if reference is None:
            return None
        if order.side == OrderSide.buy and reference <= order.limit_price:
            return self._apply_slippage(reference, order.side)
        if order.side == OrderSide.sell and reference >= order.limit_price:
            return self._apply_slippage(reference, order.side)
        return None

    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        if self._config.slippage == Decimal("0"):
            return price
        if side == OrderSide.buy:
            return price + self._config.slippage
        return price - self._config.slippage

