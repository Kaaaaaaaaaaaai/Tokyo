from datetime import UTC, datetime


class Clock:
    """UTC clock wrapper for testable timestamp generation."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock(Clock):
    def __init__(self, value: datetime) -> None:
        self._value = value if value.tzinfo else value.replace(tzinfo=UTC)

    def now(self) -> datetime:
        return self._value

