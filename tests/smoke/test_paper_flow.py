from datetime import UTC, datetime

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.contracts.market_data import MarketTick
from tokyo.packages.contracts.orders import OrderIntent


async def test_first_paper_flow_smoke() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings())
    await runtime.kill_switch.release(actor_id="smoke", reason="test")
    now = datetime.now(UTC)
    await runtime.store.add_tick(
        MarketTick(
            symbol_id="01020304",
            source="smoke",
            source_timestamp=now,
            ingested_at=now,
            bid="154.123",
            ask="154.126",
        )
    )
    result = await runtime.execution.submit_order_intent(
        OrderIntent(
            strategy_id="mean_reversion_jpy",
            account_id="paper_main",
            trading_mode="paper",
            symbol_id="01020304",
            side="buy",
            order_type="market",
            quantity="1000",
            time_in_force="day",
            client_order_id="smoke-test-000001",
        )
    )
    report = await runtime.reports.generate(report_date=now.date())
    assert result.accepted is True
    assert len(result.executions) == 1
    assert report.order_intents == 1
    assert report.fills == 1

