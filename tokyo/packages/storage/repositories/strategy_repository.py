from datetime import UTC, datetime

from sqlalchemy import select

from tokyo.packages.contracts.strategy import Strategy
from tokyo.packages.storage.models import StrategyModel
from tokyo.packages.storage.repositories.base import BaseRepository


class StrategyRepository(BaseRepository):
    async def list(self) -> list[Strategy]:
        rows = (await self.session.scalars(select(StrategyModel).order_by(StrategyModel.strategy_id))).all()
        return [self._to_contract(row) for row in rows]

    async def get(self, strategy_id: str) -> Strategy | None:
        row = await self.session.get(StrategyModel, strategy_id)
        return self._to_contract(row) if row else None

    async def set_enabled(self, strategy_id: str, enabled: bool) -> Strategy | None:
        row = await self.session.get(StrategyModel, strategy_id)
        if row is None:
            return None
        row.enabled = enabled
        row.updated_at = datetime.now(UTC)
        return self._to_contract(row)

    async def upsert(self, strategy: Strategy) -> Strategy:
        now = datetime.now(UTC)
        await self.session.merge(
            StrategyModel(
                strategy_id=strategy.strategy_id,
                enabled=strategy.enabled,
                allowed_accounts=strategy.allowed_accounts,
                allowed_symbols=strategy.allowed_symbols,
                metadata_=strategy.metadata,
                created_at=now,
                updated_at=now,
            )
        )
        return strategy

    def _to_contract(self, row: StrategyModel) -> Strategy:
        return Strategy(
            strategy_id=row.strategy_id,
            enabled=row.enabled,
            allowed_accounts=row.allowed_accounts or [],
            allowed_symbols=row.allowed_symbols or [],
            metadata=row.metadata_ or {},
        )

