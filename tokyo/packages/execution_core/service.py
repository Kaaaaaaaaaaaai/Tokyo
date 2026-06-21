import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from tokyo.packages.adapters.market.paper_market_adapter import PaperMarketAdapter
from tokyo.packages.common.clock import Clock
from tokyo.packages.common.errors import ConflictError, NotFoundError, TokyoError, ValidationFailure
from tokyo.packages.contracts.enums import ErrorCode, OrderStatus
from tokyo.packages.contracts.execution import ExecutionReport, Position
from tokyo.packages.contracts.orders import Order, OrderEvent, OrderIntent
from tokyo.packages.domain.order_state_machine import OrderStateMachine
from tokyo.packages.domain.risk_checks import RiskEngine, RiskValidationContext
from tokyo.packages.execution_core.in_memory_store import InMemoryExecutionStore


@dataclass(frozen=True, slots=True)
class OrderSubmissionResult:
    order: Order
    events: list[OrderEvent]
    executions: list[ExecutionReport]
    position: Position | None
    accepted: bool
    reason_code: str | None = None


class ExecutionService:
    """Validates order intents, routes to paper execution, and persists transitions."""

    def __init__(
        self,
        store: InMemoryExecutionStore,
        paper_adapter: PaperMarketAdapter,
        clock: Clock | None = None,
    ) -> None:
        self._store = store
        self._paper_adapter = paper_adapter
        self._clock = clock or Clock()
        self._risk = RiskEngine()
        self._state_machine = OrderStateMachine()

    async def submit_order_intent(
        self,
        intent: OrderIntent,
        correlation_id: UUID | None = None,
    ) -> OrderSubmissionResult:
        correlation_id = correlation_id or uuid4()
        payload_hash = self._payload_hash(intent)
        duplicate = await self._store.find_order_by_client_order_id(
            strategy_id=intent.strategy_id,
            account_id=intent.account_id,
            trading_mode=intent.trading_mode.value,
            client_order_id=intent.client_order_id,
        )
        if duplicate:
            if duplicate.metadata.get("payload_hash") == payload_hash:
                return OrderSubmissionResult(
                    order=duplicate,
                    events=await self._store.order_events_for(duplicate.order_id),
                    executions=[],
                    position=None,
                    accepted=duplicate.status not in {OrderStatus.rejected, OrderStatus.failed},
                )
            raise ConflictError(
                ErrorCode.client_order_id_conflict,
                "client_order_id already exists with a different payload.",
                {"client_order_id": intent.client_order_id},
                correlation_id,
            )

        now = self._clock.now()
        order = Order.from_intent(intent, now, correlation_id)
        order.metadata["payload_hash"] = payload_hash
        await self._store.create_order(order)
        events: list[OrderEvent] = [
            await self._append_event(order, None, OrderStatus.received, "received", None, None)
        ]
        try:
            order, event = await self._transition(order, OrderStatus.validating, "validation", None, None)
            events.append(event)
            await self._validate(intent, correlation_id)
            order, event = await self._transition(order, OrderStatus.accepted, "validation", None, None)
            events.append(event)
            order, event = await self._transition(order, OrderStatus.submitting, "submit", None, None)
            events.append(event)
            order, event = await self._transition(order, OrderStatus.submitted, "submit", None, None)
            events.append(event)
            execution = await self._paper_adapter.submit_order(order)
            order, event = await self._transition(order, OrderStatus.acknowledged, "ack", None, None)
            events.append(event)
            if execution is None:
                return OrderSubmissionResult(order, events, [], None, accepted=True)
            await self._store.add_execution(execution)
            symbol = await self._store.get_symbol(order.symbol_id)
            unit = symbol.unit if symbol else "USD"
            position = await self._store.update_position_from_execution(execution, unit)
            order = order.model_copy(
                update={
                    "status": OrderStatus.filled,
                    "filled_quantity": order.quantity,
                    "updated_at": self._clock.now(),
                }
            )
            await self._store.update_order(order)
            event = await self._append_event(
                order,
                OrderStatus.acknowledged,
                OrderStatus.filled,
                "fill",
                None,
                "Paper order filled.",
            )
            events.append(event)
            return OrderSubmissionResult(order, events, [execution], position, accepted=True)
        except TokyoError as exc:
            order = order.model_copy(update={"status": OrderStatus.rejected, "updated_at": self._clock.now()})
            await self._store.update_order(order)
            event = await self._append_event(
                order,
                OrderStatus.validating,
                OrderStatus.rejected,
                "reject",
                exc.code.value,
                exc.message,
                exc.details,
            )
            events.append(event)
            return OrderSubmissionResult(
                order=order,
                events=events,
                executions=[],
                position=None,
                accepted=False,
                reason_code=exc.code.value,
            )

    async def cancel_order(self, order_id: UUID, correlation_id: UUID | None = None) -> Order:
        correlation_id = correlation_id or uuid4()
        order = await self._store.get_order(order_id)
        if order is None:
            raise NotFoundError(ErrorCode.not_found, "Order not found.", {"order_id": str(order_id)}, correlation_id)
        if not self._state_machine.is_open(order.status):
            raise ValidationFailure(
                ErrorCode.order_not_open,
                "Order is not open and cannot be canceled.",
                {"status": order.status.value},
                correlation_id,
            )
        order, _ = await self._transition(order, OrderStatus.cancel_requested, "cancel", None, None)
        await self._paper_adapter.cancel_order(order)
        order, _ = await self._transition(order, OrderStatus.canceled, "cancel", None, "Paper order canceled.")
        return order

    async def cancel_open_orders(self) -> list[Order]:
        canceled: list[Order] = []
        for order in await self._store.list_orders():
            if self._state_machine.is_open(order.status):
                canceled.append(await self.cancel_order(order.order_id))
        return canceled

    async def _validate(self, intent: OrderIntent, correlation_id: UUID) -> None:
        context = RiskValidationContext(
            strategy=await self._store.get_strategy(intent.strategy_id),
            account=await self._store.get_account(intent.account_id),
            symbol=await self._store.get_symbol(intent.symbol_id),
            kill_switch_state=await self._store.get_kill_switch_state(),
            latest_price=await self._store.latest_price(intent.symbol_id),
            risk_limits=await self._store.list_risk_limits(),
            now=self._clock.now(),
            paper_adapter_healthy=True,
            correlation_id=correlation_id,
        )
        self._risk.validate(intent, context)

    async def _transition(
        self,
        order: Order,
        new_status: OrderStatus,
        event_type: str,
        reason_code: str | None,
        message: str | None,
    ) -> tuple[Order, OrderEvent]:
        previous = order.status
        self._state_machine.assert_transition(previous, new_status)
        updated = order.model_copy(update={"status": new_status, "updated_at": self._clock.now()})
        await self._store.update_order(updated)
        event = await self._append_event(updated, previous, new_status, event_type, reason_code, message)
        return updated, event

    async def _append_event(
        self,
        order: Order,
        previous_status: OrderStatus | None,
        new_status: OrderStatus,
        event_type: str,
        reason_code: str | None,
        message: str | None,
        payload: dict[str, object] | None = None,
    ) -> OrderEvent:
        event = OrderEvent(
            order_id=order.order_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            reason_code=reason_code,
            message=message,
            payload=payload or {},
            correlation_id=order.correlation_id,
            created_at=self._clock.now(),
        )
        await self._store.add_order_event(event)
        return event

    def _payload_hash(self, intent: OrderIntent) -> str:
        payload = json.dumps(intent.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

