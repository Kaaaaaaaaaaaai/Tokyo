from dataclasses import dataclass

from redis.asyncio import Redis

from tokyo.packages.adapters.market.paper_market_adapter import PaperMarketAdapter
from tokyo.packages.common.config import ConfigLoader, EventBusBackend, RuntimeSettings
from tokyo.packages.data_core.event_bus import (
    EventPublisher,
    InMemoryEventBus,
    RedisStreamPublisher,
)
from tokyo.packages.data_core.service import DataCoreService
from tokyo.packages.execution_core.in_memory_store import InMemoryExecutionStore
from tokyo.packages.execution_core.service import ExecutionService
from tokyo.packages.reporting.daily_report import DailyReportService
from tokyo.packages.supervision.alerting import WebhookAlertConfig, WebhookAlertSender
from tokyo.packages.supervision.kill_switch import KillSwitchService


@dataclass(slots=True)
class TokyoRuntime:
    settings: RuntimeSettings
    store: InMemoryExecutionStore
    event_bus: EventPublisher
    data_core: DataCoreService
    execution: ExecutionService
    kill_switch: KillSwitchService
    reports: DailyReportService
    paper_adapter: PaperMarketAdapter
    redis: Redis | None = None

    @classmethod
    async def build(cls, settings: RuntimeSettings) -> "TokyoRuntime":
        bundle = ConfigLoader(settings.config_path).load()
        store = InMemoryExecutionStore()
        await store.seed(
            symbols=bundle.symbols,
            accounts=bundle.accounts,
            strategies=bundle.strategies,
            risk_limits=bundle.risk_limits,
            kill_switch_state=settings.kill_switch_default,
        )
        redis_client: Redis | None = None
        if settings.event_bus_backend == EventBusBackend.redis:
            redis_client = Redis.from_url(settings.redis_url)
            event_bus: EventPublisher = RedisStreamPublisher(
                redis_client,
                max_len=settings.redis_stream_max_len,
            )
        else:
            event_bus = InMemoryEventBus()
        data_core = DataCoreService(event_bus)
        paper_adapter = PaperMarketAdapter(store.latest_prices)
        execution = ExecutionService(store, paper_adapter)
        alert_sender = WebhookAlertSender(
            WebhookAlertConfig(url=settings.webhook_alert_url, kind=settings.webhook_alert_kind)
        )
        kill_switch = KillSwitchService(store, execution, alert_sender)
        reports = DailyReportService(store)
        return cls(
            settings=settings,
            store=store,
            event_bus=event_bus,
            data_core=data_core,
            execution=execution,
            kill_switch=kill_switch,
            reports=reports,
            paper_adapter=paper_adapter,
            redis=redis_client,
        )

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
