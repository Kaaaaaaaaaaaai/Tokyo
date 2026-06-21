import pytest

from tokyo.packages.contracts.enums import OrderStatus
from tokyo.packages.domain.order_state_machine import OrderStateMachine


def test_valid_order_transition() -> None:
    machine = OrderStateMachine()
    machine.assert_transition(OrderStatus.received, OrderStatus.validating)


def test_invalid_order_transition_is_rejected() -> None:
    machine = OrderStateMachine()
    with pytest.raises(ValueError):
        machine.assert_transition(OrderStatus.received, OrderStatus.filled)

