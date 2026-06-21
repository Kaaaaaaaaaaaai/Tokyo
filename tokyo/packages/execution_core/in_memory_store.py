import asyncio
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from tokyo.packages.contracts.account import Account
from tokyo.packages.contracts.enums import KillSwitchState, OrderStatus
from tokyo.packages.contracts.execution import Balance, ExecutionReport, Position
from tokyo.packages.contracts.market_data import BackfillJob, BackfillRequest, MarketBar, MarketTick
from tokyo.packages.contracts.orders import Order, OrderEvent
from tokyo.packages.contracts.risk import RiskEvent, RiskLimit
from tokyo.packages.contracts.strategy import Strategy
from tokyo.packages.contracts.symbol import Symbol
from tokyo.packages.contracts.system import SystemEvent
from tokyo.packages.domain.risk_checks import LatestPrice


class InMemoryExecutionStore:
    """Process-local store for tests and the first paper MVP runtime."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.symbols: dict[str, Symbol] = {}
        self.accounts: dict[str, Account] = {}
        self.strategies: dict[str, Strategy] = {}
        self.risk_limits: dict[str, RiskLimit] = {}
        self.risk_events: list[RiskEvent] = []
        self.system_events: list[SystemEvent] = []
        self.orders: dict[UUID, Order] = {}
        self.order_events: dict[UUID, list[OrderEvent]] = defaultdict(list)
        self.executions: list[ExecutionReport] = []
        self.positions: dict[tuple[str, str, str | None], Position] = {}
        self.balances: dict[tuple[str, str], Balance] = {}
        self.latest_prices: dict[str, LatestPrice] = {}
        self.ticks: list[MarketTick] = []
        self.bars: list[MarketBar] = []
        self.backfill_jobs: dict[UUID, BackfillJob] = {}
        self.kill_switch_state = KillSwitchState.engaged

    async def seed(
        self,
        *,
        symbols: list[Symbol],
        accounts: list[Account],
        strategies: list[Strategy],
        risk_limits: list[RiskLimit],
        kill_switch_state: KillSwitchState,
    ) -> None:
        async with self._lock:
            self.symbols = {item.symbol_id: item for item in symbols}
            self.accounts = {item.account_id: item for item in accounts}
            self.strategies = {item.strategy_id: item for item in strategies}
            self.risk_limits = {item.limit_id: item for item in risk_limits}
            self.kill_switch_state = kill_switch_state
            now = datetime.now(UTC)
            for account in accounts:
                for asset, amount in account.initial_balances.items():
                    self.balances[(account.account_id, asset)] = Balance(
                        account_id=account.account_id,
                        asset=asset,
                        available=amount,
                        total=amount,
                        as_of=now,
                    )

    async def get_symbol(self, symbol_id: str) -> Symbol | None:
        return self.symbols.get(symbol_id)

    async def list_symbols(self) -> list[Symbol]:
        return list(self.symbols.values())

    async def get_strategy(self, strategy_id: str) -> Strategy | None:
        return self.strategies.get(strategy_id)

    async def list_strategies(self) -> list[Strategy]:
        return list(self.strategies.values())

    async def set_strategy_enabled(self, strategy_id: str, enabled: bool) -> Strategy | None:
        strategy = self.strategies.get(strategy_id)
        if strategy is None:
            return None
        updated = strategy.model_copy(update={"enabled": enabled})
        self.strategies[strategy_id] = updated
        return updated

    async def get_account(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    async def list_accounts(self) -> list[Account]:
        return list(self.accounts.values())

    async def list_risk_limits(self) -> list[RiskLimit]:
        return list(self.risk_limits.values())

    async def upsert_risk_limit(self, risk_limit: RiskLimit) -> RiskLimit:
        self.risk_limits[risk_limit.limit_id] = risk_limit
        return risk_limit

    async def add_risk_event(self, event: RiskEvent) -> RiskEvent:
        self.risk_events.append(event)
        return event

    async def list_risk_events(self, limit: int = 100) -> list[RiskEvent]:
        return list(reversed(self.risk_events[-limit:]))

    async def add_system_event(self, event: SystemEvent) -> SystemEvent:
        self.system_events.append(event)
        return event

    async def list_system_events(self, limit: int = 200) -> list[SystemEvent]:
        return list(reversed(self.system_events[-limit:]))

    async def get_kill_switch_state(self) -> KillSwitchState:
        return self.kill_switch_state

    async def set_kill_switch_state(self, state: KillSwitchState) -> KillSwitchState:
        self.kill_switch_state = state
        return state

    async def add_tick(self, tick: MarketTick) -> MarketTick:
        self.ticks.append(tick)
        self.latest_prices[tick.symbol_id] = LatestPrice(
            bid=tick.bid,
            ask=tick.ask,
            last=tick.last,
            close=None,
            source_timestamp=tick.source_timestamp,
            received_at=tick.ingested_at,
        )
        return tick

    async def add_bar(self, bar: MarketBar) -> MarketBar:
        self.bars.append(bar)
        self.latest_prices[bar.symbol_id] = LatestPrice(
            bid=None,
            ask=None,
            last=None,
            close=bar.close,
            source_timestamp=bar.closed_at,
            received_at=bar.closed_at,
        )
        return bar

    async def latest_price(self, symbol_id: str) -> LatestPrice | None:
        return self.latest_prices.get(symbol_id)

    async def list_ticks(self, symbol_id: str | None = None, limit: int = 500) -> list[MarketTick]:
        ticks = [item for item in self.ticks if symbol_id is None or item.symbol_id == symbol_id]
        return list(reversed(ticks[-limit:]))

    async def list_bars(
        self,
        symbol_id: str | None = None,
        interval: str | None = None,
        limit: int = 500,
    ) -> list[MarketBar]:
        bars = [
            item
            for item in self.bars
            if (symbol_id is None or item.symbol_id == symbol_id)
            and (interval is None or item.interval == interval)
        ]
        return list(reversed(bars[-limit:]))

    async def create_backfill_job(self, request: BackfillRequest) -> BackfillJob:
        job = BackfillJob(request=request)
        self.backfill_jobs[job.job_id] = job
        return job

    async def get_backfill_job(self, job_id: UUID) -> BackfillJob | None:
        return self.backfill_jobs.get(job_id)

    async def create_order(self, order: Order) -> Order:
        self.orders[order.order_id] = order
        return order

    async def update_order(self, order: Order) -> Order:
        self.orders[order.order_id] = order
        return order

    async def get_order(self, order_id: UUID) -> Order | None:
        return self.orders.get(order_id)

    async def find_order_by_client_order_id(
        self,
        *,
        strategy_id: str,
        account_id: str,
        trading_mode: str,
        client_order_id: str,
    ) -> Order | None:
        for order in self.orders.values():
            if (
                order.strategy_id == strategy_id
                and order.account_id == account_id
                and order.trading_mode.value == trading_mode
                and order.client_order_id == client_order_id
            ):
                return order
        return None

    async def list_orders(
        self,
        *,
        strategy_id: str | None = None,
        account_id: str | None = None,
        status: OrderStatus | None = None,
    ) -> list[Order]:
        values = list(self.orders.values())
        if strategy_id:
            values = [order for order in values if order.strategy_id == strategy_id]
        if account_id:
            values = [order for order in values if order.account_id == account_id]
        if status:
            values = [order for order in values if order.status == status]
        return sorted(values, key=lambda item: item.created_at, reverse=True)

    async def add_order_event(self, event: OrderEvent) -> OrderEvent:
        self.order_events[event.order_id].append(event)
        return event

    async def order_events_for(self, order_id: UUID) -> list[OrderEvent]:
        return list(self.order_events.get(order_id, []))

    async def add_execution(self, execution: ExecutionReport) -> ExecutionReport:
        self.executions.append(execution)
        return execution

    async def list_executions(
        self,
        *,
        account_id: str | None = None,
        strategy_id: str | None = None,
    ) -> list[ExecutionReport]:
        values = list(self.executions)
        if account_id:
            values = [item for item in values if item.account_id == account_id]
        if strategy_id:
            values = [item for item in values if item.strategy_id == strategy_id]
        return sorted(values, key=lambda item: item.executed_at, reverse=True)

    async def upsert_position(self, position: Position) -> Position:
        self.positions[(position.account_id, position.symbol_id, position.strategy_id)] = position
        return position

    async def get_position(
        self,
        *,
        account_id: str,
        symbol_id: str,
        strategy_id: str | None,
    ) -> Position | None:
        return self.positions.get((account_id, symbol_id, strategy_id))

    async def list_positions(self, account_id: str | None = None) -> list[Position]:
        values = list(self.positions.values())
        if account_id:
            values = [item for item in values if item.account_id == account_id]
        return values

    async def upsert_balance(self, balance: Balance) -> Balance:
        self.balances[(balance.account_id, balance.asset)] = balance
        return balance

    async def get_balance(self, account_id: str, asset: str) -> Balance | None:
        return self.balances.get((account_id, asset))

    async def list_balances(self, account_id: str | None = None) -> list[Balance]:
        values = list(self.balances.values())
        if account_id:
            values = [item for item in values if item.account_id == account_id]
        return values

    async def orders_on_date(self, day: date) -> list[Order]:
        return [order for order in self.orders.values() if order.created_at.date() == day]

    async def executions_on_date(self, day: date) -> list[ExecutionReport]:
        return [item for item in self.executions if item.executed_at.date() == day]

    async def risk_events_on_date(self, day: date) -> list[RiskEvent]:
        return [item for item in self.risk_events if item.created_at.date() == day]

    async def update_position_from_execution(self, execution: ExecutionReport, unit: str) -> Position:
        previous = await self.get_position(
            account_id=execution.account_id,
            symbol_id=execution.symbol_id,
            strategy_id=execution.strategy_id,
        )
        signed_fill = execution.quantity if execution.side.value == "buy" else -execution.quantity
        old_quantity = previous.quantity if previous else Decimal("0")
        old_average = previous.average_entry_price if previous else None
        new_quantity = old_quantity + signed_fill
        average = execution.price if old_average is None or old_quantity == 0 else old_average
        if old_quantity == 0 or (old_quantity > 0 and signed_fill > 0) or (old_quantity < 0 and signed_fill < 0):
            total_cost = (abs(old_quantity) * (old_average or Decimal("0"))) + (
                abs(signed_fill) * execution.price
            )
            average = total_cost / abs(new_quantity) if new_quantity != 0 else None
        position = Position(
            account_id=execution.account_id,
            strategy_id=execution.strategy_id,
            symbol_id=execution.symbol_id,
            trading_mode=execution.trading_mode,
            quantity=new_quantity,
            average_entry_price=average,
            mark_price=execution.price,
            realized_pnl=previous.realized_pnl if previous else Decimal("0"),
            unrealized_pnl=Decimal("0"),
            as_of=execution.received_at,
        )
        await self.upsert_position(position)
        await self._update_cash_balance(execution, unit)
        return position

    async def _update_cash_balance(self, execution: ExecutionReport, unit: str) -> None:
        notional = execution.quantity * execution.price
        sign = Decimal("-1") if execution.side.value == "buy" else Decimal("1")
        previous = await self.get_balance(execution.account_id, unit)
        old_available = previous.available if previous else Decimal("0")
        new_available = old_available + (sign * notional)
        balance = Balance(
            account_id=execution.account_id,
            asset=unit,
            available=new_available,
            total=new_available,
            as_of=execution.received_at,
        )
        await self.upsert_balance(balance)

