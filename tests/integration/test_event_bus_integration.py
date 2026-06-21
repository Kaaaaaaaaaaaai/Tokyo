import json
from typing import Any, cast

from tokyo.packages.data_core.event_bus import RedisStreamPublisher


class FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], int, bool]] = []

    async def xadd(
        self,
        stream: str,
        fields: dict[str, str],
        *,
        maxlen: int,
        approximate: bool,
    ) -> bytes:
        self.calls.append((stream, fields, maxlen, approximate))
        return b"1-0"


async def test_redis_stream_publisher_serializes_payload() -> None:
    redis = FakeRedis()
    publisher = RedisStreamPublisher(cast(Any, redis), max_len=10)

    message_id = await publisher.publish("tokyo:test", {"b": 2, "a": 1})

    assert message_id == "1-0"
    expected_payload = json.dumps(
        {"a": 1, "b": 2},
        separators=(",", ":"),
        sort_keys=True,
    )
    assert redis.calls == [
        ("tokyo:test", {"payload": expected_payload}, 10, True),
    ]
