from fastapi import APIRouter, Depends, Request

from tokyo.apps.api.utils.dependencies import get_runtime, require_idempotency_key
from tokyo.packages.common.errors import NotFoundError
from tokyo.packages.contracts.enums import ErrorCode
from tokyo.packages.contracts.strategy import Strategy

strategies_router = APIRouter(prefix="/strategies", tags=["strategies"])


@strategies_router.get("", response_model=list[Strategy])
async def strategies(
    request: Request,
) -> list[Strategy]:
    runtime = get_runtime(request)
    return await runtime.store.list_strategies()


@strategies_router.post("/{strategy_id}/enable", response_model=Strategy)
async def enable_strategy(
    strategy_id: str,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> Strategy:
    runtime = get_runtime(request)
    strategy = await runtime.store.set_strategy_enabled(strategy_id, True)
    if strategy is None:
        raise NotFoundError(
            ErrorCode.not_found,
            "Strategy not found.",
            {"strategy_id": strategy_id},
        )
    return strategy


@strategies_router.post("/{strategy_id}/disable", response_model=Strategy)
async def disable_strategy(
    strategy_id: str,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> Strategy:
    runtime = get_runtime(request)
    strategy = await runtime.store.set_strategy_enabled(strategy_id, False)
    if strategy is None:
        raise NotFoundError(
            ErrorCode.not_found,
            "Strategy not found.",
            {"strategy_id": strategy_id},
        )
    return strategy
