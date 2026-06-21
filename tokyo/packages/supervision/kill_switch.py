from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from tokyo.packages.contracts.enums import KillSwitchState, RiskSeverity
from tokyo.packages.contracts.risk import RiskEvent
from tokyo.packages.contracts.system import SystemEvent
from tokyo.packages.execution_core.in_memory_store import InMemoryExecutionStore
from tokyo.packages.execution_core.service import ExecutionService
from tokyo.packages.supervision.alerting import WebhookAlertSender


@dataclass(frozen=True, slots=True)
class KillSwitchResult:
    state: KillSwitchState
    canceled_orders: int
    disabled_strategies: int
    correlation_id: UUID


class KillSwitchService:
    def __init__(
        self,
        store: InMemoryExecutionStore,
        execution_service: ExecutionService,
        alert_sender: WebhookAlertSender,
    ) -> None:
        self._store = store
        self._execution_service = execution_service
        self._alert_sender = alert_sender

    async def engage(
        self,
        *,
        actor_id: str,
        reason: str,
        cancel_open_orders: bool,
        disable_strategies: bool,
        correlation_id: UUID | None = None,
    ) -> KillSwitchResult:
        correlation_id = correlation_id or uuid4()
        await self._store.set_kill_switch_state(KillSwitchState.engaged)
        canceled = await self._execution_service.cancel_open_orders() if cancel_open_orders else []
        disabled_count = 0
        if disable_strategies:
            for strategy in await self._store.list_strategies():
                if strategy.enabled:
                    await self._store.set_strategy_enabled(strategy.strategy_id, False)
                    disabled_count += 1
        event = RiskEvent(
            severity=RiskSeverity.critical,
            event_type="kill_switch_engaged",
            scope="global",
            message=reason,
            payload={
                "cancel_open_orders": cancel_open_orders,
                "disable_strategies": disable_strategies,
                "canceled_orders": len(canceled),
            },
            correlation_id=correlation_id,
            created_at=datetime.now(UTC),
        )
        await self._store.add_risk_event(event)
        await self._store.add_system_event(
            SystemEvent(
                event_type="operator_action",
                actor_type="operator",
                actor_id=actor_id,
                severity=RiskSeverity.info,
                message="Kill switch engaged.",
                payload={"reason": reason},
                correlation_id=correlation_id,
                created_at=datetime.now(UTC),
            )
        )
        await self._alert_sender.send(event)
        return KillSwitchResult(KillSwitchState.engaged, len(canceled), disabled_count, correlation_id)

    async def release(
        self,
        *,
        actor_id: str,
        reason: str,
        correlation_id: UUID | None = None,
    ) -> KillSwitchResult:
        correlation_id = correlation_id or uuid4()
        await self._store.set_kill_switch_state(KillSwitchState.released)
        await self._store.add_system_event(
            SystemEvent(
                event_type="operator_action",
                actor_type="operator",
                actor_id=actor_id,
                severity=RiskSeverity.info,
                message="Kill switch released for paper mode.",
                payload={"reason": reason},
                correlation_id=correlation_id,
                created_at=datetime.now(UTC),
            )
        )
        return KillSwitchResult(KillSwitchState.released, 0, 0, correlation_id)

