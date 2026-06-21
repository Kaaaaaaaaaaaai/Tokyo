from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from tokyo.packages.contracts.enums import ErrorCode


@dataclass(slots=True)
class TokyoError(Exception):
    code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    correlation_id: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class ValidationFailure(TokyoError):
    pass


class NotFoundError(TokyoError):
    pass


class ConflictError(TokyoError):
    pass
