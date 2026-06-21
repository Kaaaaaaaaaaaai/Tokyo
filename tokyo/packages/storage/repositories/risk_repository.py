from datetime import UTC, datetime

from sqlalchemy import desc, select

from tokyo.packages.contracts.enums import RiskSeverity
from tokyo.packages.contracts.risk import RiskEvent, RiskLimit
from tokyo.packages.storage.models import RiskEventModel, RiskLimitModel
from tokyo.packages.storage.repositories.base import BaseRepository


class RiskRepository(BaseRepository):
    async def list_limits(self) -> list[RiskLimit]:
        rows = (await self.session.scalars(select(RiskLimitModel).order_by(RiskLimitModel.limit_id))).all()
        return [self._limit_to_contract(row) for row in rows]

    async def upsert_limit(self, risk_limit: RiskLimit) -> RiskLimit:
        now = datetime.now(UTC)
        await self.session.merge(
            RiskLimitModel(
                limit_id=risk_limit.limit_id,
                scope=risk_limit.scope,
                scope_id=risk_limit.scope_id,
                limit_type=risk_limit.limit_type,
                threshold=risk_limit.threshold,
                action=risk_limit.action,
                enabled=risk_limit.enabled,
                metadata_=risk_limit.metadata,
                created_at=now,
                updated_at=now,
            )
        )
        return risk_limit

    async def add_event(self, event: RiskEvent) -> RiskEvent:
        self.session.add(
            RiskEventModel(
                event_id=event.event_id,
                severity=event.severity.value,
                event_type=event.event_type,
                scope=event.scope,
                scope_id=event.scope_id,
                message=event.message,
                payload=event.payload,
                correlation_id=event.correlation_id,
                created_at=event.created_at,
            )
        )
        return event

    async def list_events(self, limit: int = 100) -> list[RiskEvent]:
        rows = (
            await self.session.scalars(select(RiskEventModel).order_by(desc(RiskEventModel.created_at)).limit(limit))
        ).all()
        return [self._event_to_contract(row) for row in rows]

    def _limit_to_contract(self, row: RiskLimitModel) -> RiskLimit:
        return RiskLimit(
            limit_id=row.limit_id,
            scope=row.scope,
            scope_id=row.scope_id,
            limit_type=row.limit_type,
            threshold=row.threshold,
            action=row.action,
            enabled=row.enabled,
            metadata=row.metadata_ or {},
        )

    def _event_to_contract(self, row: RiskEventModel) -> RiskEvent:
        return RiskEvent(
            event_id=row.event_id,
            severity=RiskSeverity(row.severity),
            event_type=row.event_type,
            scope=row.scope,
            scope_id=row.scope_id,
            message=row.message,
            payload=row.payload or {},
            correlation_id=row.correlation_id,
            created_at=row.created_at,
        )

