from datetime import date
from decimal import Decimal

from tokyo.packages.contracts.enums import OrderStatus, TradingMode
from tokyo.packages.contracts.reports import DailyReport
from tokyo.packages.execution_core.in_memory_store import InMemoryExecutionStore


class DailyReportService:
    def __init__(self, store: InMemoryExecutionStore) -> None:
        self._store = store

    async def generate(
        self,
        *,
        report_date: date,
        trading_mode: TradingMode = TradingMode.paper,
        account_id: str | None = None,
        strategy_id: str | None = None,
    ) -> DailyReport:
        orders = [
            order
            for order in await self._store.orders_on_date(report_date)
            if order.trading_mode == trading_mode
            and (account_id is None or order.account_id == account_id)
            and (strategy_id is None or order.strategy_id == strategy_id)
        ]
        executions = [
            execution
            for execution in await self._store.executions_on_date(report_date)
            if execution.trading_mode == trading_mode
            and (account_id is None or execution.account_id == account_id)
            and (strategy_id is None or execution.strategy_id == strategy_id)
        ]
        positions = [
            position
            for position in await self._store.list_positions(account_id)
            if position.trading_mode == trading_mode
            and (strategy_id is None or position.strategy_id == strategy_id)
        ]
        gross_exposure = sum(
            (abs(position.quantity) * (position.mark_price or Decimal("0"))) for position in positions
        )
        net_exposure = sum(
            (position.quantity * (position.mark_price or Decimal("0"))) for position in positions
        )
        largest_position = None
        if positions:
            largest = max(
                positions,
                key=lambda item: abs(item.quantity) * (item.mark_price or Decimal("0")),
            )
            largest_position = largest.model_dump(mode="json")
        return DailyReport(
            date=report_date,
            trading_mode=trading_mode,
            account_id=account_id,
            strategy_id=strategy_id,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            order_intents=len(orders),
            accepted_orders=len([order for order in orders if order.status != OrderStatus.rejected]),
            rejected_orders=len([order for order in orders if order.status == OrderStatus.rejected]),
            fills=len(executions),
            cancel_requests=len([order for order in orders if order.status == OrderStatus.cancel_requested]),
            risk_alerts=len(await self._store.risk_events_on_date(report_date)),
            largest_position=largest_position,
        )

