from sqlalchemy import desc, select

from tokyo.packages.contracts.enums import RiskSeverity
from tokyo.packages.contracts.system import SystemEvent
from tokyo.packages.storage.models import SystemEventModel
from tokyo.packages.storage.repositories.base import BaseRepository


class SystemEventRepository(BaseRepository):
    async def add(self, event: SystemEvent) -> SystemEvent:
        self.session.add(
            SystemEventModel(
                event_id=event.event_id,
                event_type=event.event_type,
                actor_type=event.actor_type,
                actor_id=event.actor_id,
                severity=event.severity.value,
                message=event.message,
                payload=event.payload,
                correlation_id=event.correlation_id,
                created_at=event.created_at,
            )
        )
        return event

    async def list(self, limit: int = 200) -> list[SystemEvent]:
        rows = (
            await self.session.scalars(
                select(SystemEventModel).order_by(desc(SystemEventModel.created_at)).limit(limit)
            )
        ).all()
        return [
            SystemEvent(
                event_id=row.event_id,
                event_type=row.event_type,
                actor_type=row.actor_type,
                actor_id=row.actor_id,
                severity=RiskSeverity(row.severity),
                message=row.message,
                payload=row.payload or {},
                correlation_id=row.correlation_id,
                created_at=row.created_at,
            )
            for row in rows
        ]

