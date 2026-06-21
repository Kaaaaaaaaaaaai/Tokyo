from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer, WithJsonSchema

DECIMAL_PATTERN = r"^-?(0|[1-9]\d*)(\.\d+)?$"


def parse_decimal_string(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("decimal value must be finite")
        return value
    if isinstance(value, bool | float | int):
        raise ValueError("decimal value must be a string, not a JSON number")
    if not isinstance(value, str):
        raise ValueError("decimal value must be a string")
    if value != value.strip() or not value:
        raise ValueError("decimal value must not contain surrounding whitespace")
    lowered = value.lower()
    if "e" in lowered or "nan" in lowered or "inf" in lowered:
        raise ValueError("decimal value must be a plain finite decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("decimal value is not valid") from exc
    if not parsed.is_finite():
        raise ValueError("decimal value must be finite")
    return parsed


def serialize_decimal_string(value: Decimal) -> str:
    return format(value, "f")


DecimalString = Annotated[
    Decimal,
    BeforeValidator(parse_decimal_string),
    PlainSerializer(serialize_decimal_string, return_type=str),
    WithJsonSchema({"type": "string", "pattern": DECIMAL_PATTERN}),
]


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class TokyoBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

