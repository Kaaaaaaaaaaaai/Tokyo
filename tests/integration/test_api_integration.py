from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.apps.api.utils.app_factory import create_app
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.contracts.market_data import MarketTick
from tokyo.packages.data_core.event_bus import InMemoryEventBus, StreamNames


async def test_health_and_symbols_api() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings(TOKYO_API_KEY="test-api-key"))
    app = create_app()
    app.state.runtime = runtime
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            health = await client.get("/api/v1/health")
            assert health.status_code == 200
            assert health.json()["status"] == "ok"

            unauthenticated = await client.get("/api/v1/symbols")
            assert unauthenticated.status_code == 401

            response = await client.get(
                "/api/v1/symbols",
                headers={"X-API-Key": "test-api-key"},
            )
            assert response.status_code == 200
            assert any(item["symbol_id"] == "01020304" for item in response.json())
    finally:
        await runtime.close()


async def test_data_core_publishes_market_ticks_to_runtime_event_bus() -> None:
    runtime = await TokyoRuntime.build(RuntimeSettings())
    try:
        assert isinstance(runtime.event_bus, InMemoryEventBus)
        now = datetime.now(UTC)
        tick = MarketTick(
            symbol_id="01020304",
            source="integration",
            source_timestamp=now,
            ingested_at=now,
            bid="154.123",
            ask="154.126",
        )

        await runtime.data_core.ingest_tick(tick)

        stream = StreamNames.market_data("market.tick.01020304")
        events = runtime.event_bus.replay(stream, 0)
        assert len(events) == 1
        assert events[0]["symbol_id"] == "01020304"
        assert events[0]["source"] == "integration"
    finally:
        await runtime.close()
