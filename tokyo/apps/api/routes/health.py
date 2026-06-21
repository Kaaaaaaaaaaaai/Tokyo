from uuid import uuid4

from fastapi import APIRouter, Request

from tokyo.apps.api.utils.dependencies import get_runtime
from tokyo.packages.contracts.api import HealthResponse

health_router = APIRouter(tags=["health"])


@health_router.get("/api/v1/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    runtime = get_runtime(request)
    return HealthResponse(
        status="ok",
        service="tokyo-api",
        dependencies={
            "postgres": "configured",
            "redis": "configured",
            "kill_switch": (await runtime.store.get_kill_switch_state()).value,
        },
        correlation_id=uuid4(),
    )

