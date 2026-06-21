from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from tokyo.apps.api.utils.dependencies import get_runtime, require_idempotency_key
from tokyo.packages.common.errors import NotFoundError
from tokyo.packages.contracts.enums import ErrorCode
from tokyo.packages.contracts.market_data import BackfillJob, BackfillRequest, MarketBar, MarketTick

data_router = APIRouter(prefix="/data", tags=["data"])


@data_router.get("/ticks", response_model=list[MarketTick])
async def ticks(
    request: Request,
    symbol_id: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[MarketTick]:
    runtime = get_runtime(request)
    return await runtime.store.list_ticks(symbol_id, limit)


@data_router.get("/bars", response_model=list[MarketBar])
async def bars(
    request: Request,
    symbol_id: str | None = None,
    interval: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[MarketBar]:
    runtime = get_runtime(request)
    return await runtime.store.list_bars(symbol_id, interval, limit)


@data_router.post("/backfills", response_model=BackfillJob)
async def start_backfill(
    request_body: BackfillRequest,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key),
) -> BackfillJob:
    runtime = get_runtime(request)
    return await runtime.store.create_backfill_job(request_body)


@data_router.get("/backfills/{job_id}", response_model=BackfillJob)
async def backfill_status(
    job_id: UUID,
    request: Request,
) -> BackfillJob:
    runtime = get_runtime(request)
    job = await runtime.store.get_backfill_job(job_id)
    if job is None:
        raise NotFoundError(ErrorCode.not_found, "Backfill job not found.", {"job_id": str(job_id)})
    return job
