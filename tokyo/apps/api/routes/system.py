from fastapi import APIRouter, Request

from tokyo.apps.api.utils.dependencies import get_runtime
from tokyo.packages.contracts.execution import Balance
from tokyo.packages.contracts.system import SystemEvent

system_router = APIRouter(tags=["system"])


@system_router.get("/system/events", response_model=list[SystemEvent])
async def system_events(
    request: Request,
) -> list[SystemEvent]:
    runtime = get_runtime(request)
    return await runtime.store.list_system_events()


@system_router.get("/balances", response_model=list[Balance])
async def balances(
    request: Request,
    account_id: str | None = None,
) -> list[Balance]:
    runtime = get_runtime(request)
    return await runtime.store.list_balances(account_id)
