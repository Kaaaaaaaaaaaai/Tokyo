from datetime import UTC, datetime

from tokyo.packages.contracts.market_data import MarketBar, MarketTick
from tokyo.packages.data_core.event_bus import EventPublisher, StreamNames


class DataCoreService:
    """Validates, stores, and publishes canonical market data events."""

    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher
        self._latest_ticks: dict[str, MarketTick] = {}
        self._latest_bars: dict[tuple[str, str], MarketBar] = {}

    async def ingest_tick(self, tick: MarketTick) -> MarketTick:
        if tick.ingested_at.tzinfo is None:
            tick.ingested_at = tick.ingested_at.replace(tzinfo=UTC)
        previous = self._latest_ticks.get(tick.symbol_id)
        if previous and tick.source_timestamp <= previous.source_timestamp:
            tick.quality.is_out_of_order = tick.source_timestamp < previous.source_timestamp
            tick.quality.is_duplicate = tick.source_timestamp == previous.source_timestamp
        self._latest_ticks[tick.symbol_id] = tick
        channel = f"market.tick.{tick.symbol_id}"
        await self._publisher.publish(StreamNames.market_data(channel), tick.model_dump(mode="json"))
        return tick

    async def ingest_bar(self, bar: MarketBar) -> MarketBar:
        self._latest_bars[(bar.symbol_id, bar.interval)] = bar
        channel = f"market.bar.{bar.symbol_id}.{bar.interval}"
        await self._publisher.publish(StreamNames.market_data(channel), bar.model_dump(mode="json"))
        return bar

    def latest_tick(self, symbol_id: str) -> MarketTick | None:
        return self._latest_ticks.get(symbol_id)

    def latest_bar(self, symbol_id: str, interval: str) -> MarketBar | None:
        return self._latest_bars.get((symbol_id, interval))

    def mark_stale(self, symbol_id: str, threshold_seconds: int) -> bool:
        tick = self._latest_ticks.get(symbol_id)
        if tick is None:
            return True
        age = datetime.now(UTC) - tick.source_timestamp
        stale = age.total_seconds() > threshold_seconds
        tick.quality.is_stale = stale
        return stale

