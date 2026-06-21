from tokyo.packages.contracts.enums import OrderStatus


class OrderStateMachine:
    """Order lifecycle transition validator."""

    _transitions: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.received: {OrderStatus.validating},
        OrderStatus.validating: {OrderStatus.rejected, OrderStatus.accepted},
        OrderStatus.accepted: {OrderStatus.submitting, OrderStatus.cancel_requested},
        OrderStatus.submitting: {OrderStatus.submitted, OrderStatus.failed},
        OrderStatus.submitted: {OrderStatus.acknowledged, OrderStatus.rejected},
        OrderStatus.acknowledged: {
            OrderStatus.partially_filled,
            OrderStatus.filled,
            OrderStatus.cancel_requested,
            OrderStatus.expired,
        },
        OrderStatus.partially_filled: {
            OrderStatus.partially_filled,
            OrderStatus.filled,
            OrderStatus.cancel_requested,
        },
        OrderStatus.cancel_requested: {
            OrderStatus.canceled,
            OrderStatus.partially_filled,
            OrderStatus.filled,
            OrderStatus.cancel_rejected,
        },
        OrderStatus.cancel_rejected: {OrderStatus.acknowledged},
        OrderStatus.failed: {OrderStatus.unknown},
        OrderStatus.unknown: {OrderStatus.reconciled},
        OrderStatus.reconciled: {
            OrderStatus.acknowledged,
            OrderStatus.filled,
            OrderStatus.canceled,
            OrderStatus.rejected,
        },
        OrderStatus.rejected: set(),
        OrderStatus.filled: set(),
        OrderStatus.canceled: set(),
        OrderStatus.expired: set(),
    }

    def can_transition(self, previous: OrderStatus, new: OrderStatus) -> bool:
        return new in self._transitions[previous]

    def assert_transition(self, previous: OrderStatus, new: OrderStatus) -> None:
        if not self.can_transition(previous, new):
            msg = f"invalid order transition {previous.value} -> {new.value}"
            raise ValueError(msg)

    def is_open(self, status: OrderStatus) -> bool:
        return status in {
            OrderStatus.accepted,
            OrderStatus.submitting,
            OrderStatus.submitted,
            OrderStatus.acknowledged,
            OrderStatus.partially_filled,
            OrderStatus.cancel_rejected,
        }

