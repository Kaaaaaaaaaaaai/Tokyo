from decimal import Decimal

import pytest
from pydantic import ValidationError

from tokyo.packages.contracts.orders import OrderIntent


def test_decimal_strings_round_trip_exactly() -> None:
    intent = OrderIntent(
        strategy_id="mean_reversion_jpy",
        account_id="paper_main",
        trading_mode="paper",
        symbol_id="01020304",
        side="buy",
        order_type="market",
        quantity="0.1",
        time_in_force="day",
        client_order_id="decimal-test",
    )
    assert intent.quantity + Decimal("0.2") == Decimal("0.3")
    assert intent.model_dump(mode="json")["quantity"] == "0.1"


def test_money_fields_reject_binary_float() -> None:
    with pytest.raises(ValidationError):
        OrderIntent(
            strategy_id="mean_reversion_jpy",
            account_id="paper_main",
            trading_mode="paper",
            symbol_id="01020304",
            side="buy",
            order_type="market",
            quantity=0.1,
            time_in_force="day",
            client_order_id="float-test",
        )

