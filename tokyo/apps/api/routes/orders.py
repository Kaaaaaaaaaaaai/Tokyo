from uuid import UUID

from fastapi import APIRouter, Depends, Request

from tokyo.apps.api.utils.dependencies import get_runtime, require_idempotency_key
from tokyo.packages.common.errors import NotFoundError
from tokyo.packages.contracts.enums import ErrorCode, OrderStatus
from tokyo.packages.contracts.execution import ExecutionReport, Position
from tokyo.packages.contracts.orders import Order, OrderDetail

orders_router = APIRouter(tags=["orders"])


@orders_router.get("/orders", response_model=list[Order])
async def list_orders(
    request: Request,
    strategy_id: str | None = None,
    account_id: str | None = None,
    status: OrderStatus | None = None,
) -> list[Order]:
    runtime = get_runtime(request)
    return await runtime.store.list_orders(
        strategy_id=strategy_id,
        account_id=account_id,
        status=status,
    )


@orders_router.get("/orders/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: UUID,
    request: Request,
) -> OrderDetail:
    runtime = get_runtime(request)
    order = await runtime.store.get_order(order_id)
    if order is None:
        raise NotFoundError(ErrorCode.not_found, "Order not found.", {"order_id": str(order_id)})
    return OrderDetail(order=order, events=await runtime.store.order_events_for(order_id))


@orders_router.post("/orders/{order_id}/cancel", response_model=Order)
async def cancel_order(
    order_id: UUID,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> Order:
    runtime = get_runtime(request)
    return await runtime.execution.cancel_order(order_id)


@orders_router.get("/executions", response_model=list[ExecutionReport])
async def list_executions(
    request: Request,
    account_id: str | None = None,
    strategy_id: str | None = None,
) -> list[ExecutionReport]:
    runtime = get_runtime(request)
    return await runtime.store.list_executions(account_id=account_id, strategy_id=strategy_id)


@orders_router.get("/positions", response_model=list[Position])
async def list_positions(
    request: Request,
    account_id: str | None = None,
) -> list[Position]:
    runtime = get_runtime(request)
    return await runtime.store.list_positions(account_id)
