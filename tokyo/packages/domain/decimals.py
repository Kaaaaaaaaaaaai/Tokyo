from decimal import Decimal

from tokyo.packages.contracts.base import parse_decimal_string


class DecimalRules:
    """Decimal helpers for money, quantity, and price validation."""

    @staticmethod
    def parse(value: str | Decimal) -> Decimal:
        return parse_decimal_string(value)

    @staticmethod
    def is_positive(value: Decimal) -> bool:
        return value > Decimal("0")

    @staticmethod
    def is_multiple(value: Decimal, increment: Decimal | None) -> bool:
        if increment is None or increment == Decimal("0"):
            return True
        if increment < Decimal("0"):
            return False
        return (value / increment) == (value / increment).to_integral_value()

    @staticmethod
    def notional(quantity: Decimal, price: Decimal | None) -> Decimal | None:
        if price is None:
            return None
        return quantity * price

