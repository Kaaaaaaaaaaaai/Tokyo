from collections.abc import AsyncIterator

from tokyo.packages.contracts.adapters import AdapterCapabilities, AdapterHealth
from tokyo.packages.contracts.execution import Balance, ExecutionReport, Position
from tokyo.packages.contracts.orders import Order


class MarketAdapter:
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

    async def submit_order(self, order: Order) -> ExecutionReport | None:
        raise NotImplementedError

    async def cancel_order(self, order: Order) -> None:
        raise NotImplementedError

    async def stream_execution_reports(self) -> AsyncIterator[ExecutionReport]:
        raise NotImplementedError
        yield

    async def fetch_positions(self) -> list[Position]:
        raise NotImplementedError

    async def fetch_balances(self) -> list[Balance]:
        raise NotImplementedError

