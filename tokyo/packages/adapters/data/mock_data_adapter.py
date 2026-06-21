from collections.abc import AsyncIterator
from datetime import UTC, datetime

from tokyo.packages.contracts.adapters import AdapterCapabilities, AdapterHealth
from tokyo.packages.contracts.enums import AdapterState
from tokyo.packages.contracts.market_data import BackfillRequest, MarketTick
from tokyo.packages.contracts.symbol import Symbol
from tokyo.packages.adapters.data.base import CanonicalMarketEvent, DataAdapter


class MockDataAdapter(DataAdapter):
    adapter_id = "mock_data"
    adapter_type = "data"
    version = "0.1.0"

    def __init__(self, symbols: list[Symbol]) -> None:
        self._symbols = symbols
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def health(self) -> AdapterHealth:
        state = AdapterState.healthy if self._running else AdapterState.disabled
        return AdapterHealth(
            adapter_id=self.adapter_id,
            adapter_type=self.adapter_type,
            state=state,
            checked_at=datetime.now(UTC),
        )

    async def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_id=self.adapter_id,
            adapter_type=self.adapter_type,
            version=self.version,
            provider="mock",
            supports_live=True,
            supports_backfill=True,
            supports_ticks=True,
            supports_bars=True,
            supports_bid_ask=True,
            symbols=[{"symbol_id": symbol.symbol_id, "symbol": symbol.symbol} for symbol in self._symbols],
        )

    async def subscribe(self, symbols: list[Symbol], channels: list[str]) -> None:
        self._running = True

    async def unsubscribe(self, symbols: list[Symbol], channels: list[str]) -> None:
        return None

    async def backfill(self, request: BackfillRequest) -> AsyncIterator[CanonicalMarketEvent]:
        now = datetime.now(UTC)
        for symbol_id in request.symbol_ids:
            yield MarketTick(
                symbol_id=symbol_id,
                source=self.adapter_id,
                source_timestamp=now,
                ingested_at=now,
                bid="100.00",
                ask="100.01",
            )

