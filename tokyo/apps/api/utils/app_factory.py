from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError

from tokyo.apps.api.routes.adapters import adapters_router
from tokyo.apps.api.routes.data import data_router
from tokyo.apps.api.routes.health import health_router
from tokyo.apps.api.routes.orders import orders_router
from tokyo.apps.api.routes.reports import reports_router
from tokyo.apps.api.routes.risk import risk_router
from tokyo.apps.api.routes.strategies import strategies_router
from tokyo.apps.api.routes.symbols import symbols_router
from tokyo.apps.api.routes.system import system_router
from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.apps.api.utils.dependencies import require_api_key
from tokyo.apps.api.utils.error_handlers import tokyo_error_handler, validation_error_handler
from tokyo.apps.api.websocket import websocket_router
from tokyo.packages.common.config import RuntimeSettings
from tokyo.packages.common.errors import TokyoError
from tokyo.packages.common.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = RuntimeSettings.from_environment()
    configure_logging(settings.log_level)
    app.state.runtime = await TokyoRuntime.build(settings)
    try:
        yield
    finally:
        await app.state.runtime.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Tokyo API", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(TokyoError, tokyo_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(health_router)
    protected_dependencies = [Depends(require_api_key)]
    app.include_router(symbols_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(data_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(orders_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(strategies_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(risk_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(reports_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(system_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(adapters_router, prefix="/api/v1", dependencies=protected_dependencies)
    app.include_router(websocket_router)
    return app
