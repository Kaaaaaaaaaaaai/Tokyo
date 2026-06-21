import asyncio
import json
from datetime import UTC, datetime

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.contracts.market_data import MarketTick
from tokyo.packages.contracts.orders import OrderIntent


async def run() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings.from_environment())
    await runtime.kill_switch.release(actor_id="smoke", reason="paper_smoke_test")
    now = datetime.now(UTC)
    tick = MarketTick(
        symbol_id="01020304",
        source="smoke",
        source_timestamp=now,
        ingested_at=now,
        bid="154.123",
        ask="154.126",
    )
    await runtime.store.add_tick(tick)
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
            client_order_id="smoke-paper-000001",
        )
    )
    report = await runtime.reports.generate(report_date=now.date())
    print(
        json.dumps(
            {
                "accepted": result.accepted,
                "order": result.order.model_dump(mode="json"),
                "executions": [item.model_dump(mode="json") for item in result.executions],
                "report": report.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

