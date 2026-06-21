import json
from collections import defaultdict
from typing import Any

from redis.asyncio import Redis


class EventPublisher:
    async def publish(self, stream: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError


class InMemoryEventBus(EventPublisher):
    def __init__(self) -> None:
        self._streams: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def publish(self, stream: str, payload: dict[str, Any]) -> str:
        self._streams[stream].append(payload)
        return str(len(self._streams[stream]))

    def replay(self, stream: str, last_seen_sequence: int) -> list[dict[str, Any]]:
        events = self._streams.get(stream, [])
        return events[last_seen_sequence:]


class RedisStreamPublisher(EventPublisher):
    def __init__(self, redis: Redis, max_len: int = 50_000) -> None:
        self._redis = redis
        self._max_len = max_len

    async def publish(self, stream: str, payload: dict[str, Any]) -> str:
        message_id = await self._redis.xadd(
            stream,
            {"payload": json.dumps(payload, separators=(",", ":"), sort_keys=True)},
            maxlen=self._max_len,
            approximate=True,
        )
        return message_id.decode("utf-8") if isinstance(message_id, bytes) else str(message_id)


class StreamNames:
    @staticmethod
    def market_data(channel: str) -> str:
        return f"tokyo:market_data:{channel}"

    @staticmethod
    def order_events(strategy_id: str) -> str:
        return f"tokyo:order_events:{strategy_id}"

    @staticmethod
    def execution_reports(strategy_id: str) -> str:
        return f"tokyo:execution_reports:{strategy_id}"

    @staticmethod
    def position_snapshots(account_id: str) -> str:
        return f"tokyo:position_snapshots:{account_id}"

    @staticmethod
    def risk_alerts(scope: str) -> str:
        return f"tokyo:risk_alerts:{scope}"

    @staticmethod
    def system_health() -> str:
        return "tokyo:system_health"

