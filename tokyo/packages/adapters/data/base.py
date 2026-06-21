from collections.abc import AsyncIterator

from tokyo.packages.contracts.adapters import AdapterCapabilities, AdapterHealth
from tokyo.packages.contracts.market_data import BackfillRequest, DatasetRecord, MarketBar, MarketTick
from tokyo.packages.contracts.symbol import Symbol

CanonicalMarketEvent = MarketTick | MarketBar


class DataAdapter:
    adapter_id: str
    adapter_type: str
    version: str

    async def start(self) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError

    async def health(self) -> AdapterHealth:
        raise NotImplementedError

    async def capabilities(self) -> AdapterCapabilities:
        raise NotImplementedError

    async def subscribe(self, symbols: list[Symbol], channels: list[str]) -> None:
        raise NotImplementedError

    async def unsubscribe(self, symbols: list[Symbol], channels: list[str]) -> None:
        raise NotImplementedError

    async def backfill(self, request: BackfillRequest) -> AsyncIterator[CanonicalMarketEvent]:
        raise NotImplementedError
        yield

    async def fetch_dataset(self, request: BackfillRequest) -> AsyncIterator[DatasetRecord]:
        raise NotImplementedError
        yield

