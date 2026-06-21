from fastapi import APIRouter, Request

from tokyo.apps.api.utils.dependencies import get_runtime

adapters_router = APIRouter(tags=["adapters"])


@adapters_router.get("/adapters")
async def adapters(
    request: Request,
) -> list[dict[str, object]]:
    runtime = get_runtime(request)
    health = await runtime.paper_adapter.health()
    capabilities = await runtime.paper_adapter.capabilities()
    return [
        {
            "health": health.model_dump(mode="json"),
            "capabilities": capabilities.model_dump(mode="json"),
        }
    ]
