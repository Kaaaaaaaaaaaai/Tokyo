from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from tokyo.apps.api.utils.dependencies import get_runtime, require_idempotency_key
from tokyo.packages.contracts.risk import RiskLimit, RiskStatus

risk_router = APIRouter(prefix="/risk", tags=["risk"])
MVP_ACTOR_ID = "mvp-operator"


class KillSwitchRequest(BaseModel):
    reason: str = Field(min_length=1)
    cancel_open_orders: bool = True
    disable_strategies: bool = False


class ReleaseKillSwitchRequest(BaseModel):
    reason: str = Field(default="paper_mode_operator_release", min_length=1)


@risk_router.get("/status", response_model=RiskStatus)
async def risk_status(
    request: Request,
) -> RiskStatus:
    runtime = get_runtime(request)
    return RiskStatus(
        kill_switch_state=await runtime.store.get_kill_switch_state(),
        active_limits=await runtime.store.list_risk_limits(),
        risk_events=await runtime.store.list_risk_events(20),
        correlation_id=uuid4(),
    )


@risk_router.get("/limits", response_model=list[RiskLimit])
async def risk_limits(
    request: Request,
) -> list[RiskLimit]:
    runtime = get_runtime(request)
    return await runtime.store.list_risk_limits()


@risk_router.put("/limits/{limit_id}", response_model=RiskLimit)
async def upsert_risk_limit(
    limit_id: str,
    risk_limit: RiskLimit,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> RiskLimit:
    runtime = get_runtime(request)
    return await runtime.store.upsert_risk_limit(
        risk_limit.model_copy(update={"limit_id": limit_id})
    )


@risk_router.post("/kill-switch/engage")
async def engage_kill_switch(
    body: KillSwitchRequest,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict[str, object]:
    runtime = get_runtime(request)
    result = await runtime.kill_switch.engage(
        actor_id=MVP_ACTOR_ID,
        reason=body.reason,
        cancel_open_orders=body.cancel_open_orders,
        disable_strategies=body.disable_strategies,
    )
    return {
        "kill_switch_state": result.state.value,
        "cancel_open_orders": body.cancel_open_orders,
        "disable_strategies": body.disable_strategies,
        "canceled_orders": result.canceled_orders,
        "disabled_strategies": result.disabled_strategies,
        "correlation_id": str(result.correlation_id),
    }


@risk_router.post("/kill-switch/release")
async def release_kill_switch(
    body: ReleaseKillSwitchRequest,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict[str, object]:
    runtime = get_runtime(request)
    result = await runtime.kill_switch.release(actor_id=MVP_ACTOR_ID, reason=body.reason)
    return {
        "kill_switch_state": result.state.value,
        "correlation_id": str(result.correlation_id),
    }
