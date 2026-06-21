from fastapi import APIRouter, Request

from tokyo.apps.api.utils.dependencies import get_runtime
from tokyo.packages.common.errors import NotFoundError
from tokyo.packages.contracts.enums import ErrorCode
from tokyo.packages.contracts.symbol import Symbol

symbols_router = APIRouter(tags=["symbols"])


@symbols_router.get("/symbols", response_model=list[Symbol])
async def list_symbols(
    request: Request,
) -> list[Symbol]:
    runtime = get_runtime(request)
    return await runtime.store.list_symbols()


@symbols_router.get("/symbols/{symbol_id}", response_model=Symbol)
async def get_symbol(
    symbol_id: str,
    request: Request,
) -> Symbol:
    runtime = get_runtime(request)
    symbol = await runtime.store.get_symbol(symbol_id)
    if symbol is None:
        raise NotFoundError(ErrorCode.not_found, "Symbol not found.", {"symbol_id": symbol_id})
    return symbol
