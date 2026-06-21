import asyncio
import json
from datetime import UTC, datetime, timedelta

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.contracts.market_data import BackfillRequest


async def run() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings.from_environment())
    now = datetime.now(UTC)
    job = await runtime.store.create_backfill_job(
        BackfillRequest(
            adapter_id="mock_data",
            symbol_ids=["01020304"],
            event_type="market.tick",
            start=now - timedelta(minutes=5),
            end=now,
        )
    )
    print(json.dumps(job.model_dump(mode="json"), indent=2, sort_keys=True))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

