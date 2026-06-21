from datetime import UTC, datetime

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.contracts.enums import OrderStatus
from tokyo.packages.contracts.market_data import MarketTick
from tokyo.packages.contracts.orders import OrderIntent


async def test_order_intent_rejected_when_kill_switch_engaged() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings())
    now = datetime.now(UTC)
    await runtime.store.add_tick(
        MarketTick(
            symbol_id="01020304",
            source="test",
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
            client_order_id="kill-switch-test",
        )
    )
    assert result.accepted is False
    assert result.reason_code == "KILL_SWITCH_ENGAGED"
    assert result.order.status == OrderStatus.rejected


async def test_paper_market_order_fills_at_latest_ask() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings())
    await runtime.kill_switch.release(actor_id="test", reason="unit_test")
    now = datetime.now(UTC)
    await runtime.store.add_tick(
        MarketTick(
            symbol_id="01020304",
            source="test",
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
            client_order_id="paper-fill-test",
        )
    )
    assert result.accepted is True
    assert result.order.status == OrderStatus.filled
    assert result.executions[0].price == "154.126"
    assert result.position is not None
    assert result.position.quantity == "1000"

