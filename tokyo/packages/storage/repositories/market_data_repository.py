from datetime import datetime

from sqlalchemy import desc, select

from tokyo.packages.contracts.market_data import MarketBar, MarketTick
from tokyo.packages.storage.models import MarketBarModel, MarketTickModel
from tokyo.packages.storage.repositories.base import BaseRepository


class MarketDataRepository(BaseRepository):
    async def add_tick(self, tick: MarketTick) -> MarketTick:
        self.session.add(
            MarketTickModel(
                event_id=tick.event_id,
                symbol_id=tick.symbol_id,
                source=tick.source,
                source_event_id=tick.source_event_id,
                source_sequence=tick.source_sequence,
                source_timestamp=tick.source_timestamp,
                ingested_at=tick.ingested_at,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                quality=tick.quality.model_dump(mode="json"),
                metadata_=tick.metadata,
            )
        )
        return tick

    async def add_bar(self, bar: MarketBar) -> MarketBar:
        self.session.add(
            MarketBarModel(
                event_id=bar.event_id,
                symbol_id=bar.symbol_id,
                source=bar.source,
                interval=bar.interval,
                opened_at=bar.opened_at,
                closed_at=bar.closed_at,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                trade_count=bar.trade_count,
                vwap=bar.vwap,
                quality=bar.quality.model_dump(mode="json"),
                metadata_=bar.metadata,
            )
        )
        return bar

    async def query_ticks(
        self,
        *,
        symbol_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[MarketTick]:
        statement = select(MarketTickModel).where(MarketTickModel.symbol_id == symbol_id)
        if start:
            statement = statement.where(MarketTickModel.source_timestamp >= start)
        if end:
            statement = statement.where(MarketTickModel.source_timestamp < end)
        rows = (
            await self.session.scalars(
                statement.order_by(desc(MarketTickModel.source_timestamp)).limit(limit)
            )
        ).all()
        return [self._tick_to_contract(row) for row in rows]

    async def query_bars(
        self,
        *,
        symbol_id: str,
        interval: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[MarketBar]:
        statement = select(MarketBarModel).where(
            MarketBarModel.symbol_id == symbol_id,
            MarketBarModel.interval == interval,
        )
        if start:
            statement = statement.where(MarketBarModel.opened_at >= start)
        if end:
            statement = statement.where(MarketBarModel.opened_at < end)
        rows = (
            await self.session.scalars(statement.order_by(desc(MarketBarModel.opened_at)).limit(limit))
        ).all()
        return [self._bar_to_contract(row) for row in rows]

    def _tick_to_contract(self, row: MarketTickModel) -> MarketTick:
        return MarketTick(
            event_id=row.event_id,
            symbol_id=row.symbol_id,
            source=row.source,
            source_event_id=row.source_event_id,
            source_sequence=row.source_sequence,
            source_timestamp=row.source_timestamp,
            ingested_at=row.ingested_at,
            bid=row.bid,
            ask=row.ask,
            last=row.last,
            volume=row.volume,
            quality=row.quality,
            metadata=row.metadata_ or {},
        )

    def _bar_to_contract(self, row: MarketBarModel) -> MarketBar:
        return MarketBar(
            event_id=row.event_id,
            symbol_id=row.symbol_id,
            source=row.source,
            interval=row.interval,
            opened_at=row.opened_at,
            closed_at=row.closed_at,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            trade_count=row.trade_count,
            vwap=row.vwap,
            quality=row.quality,
            metadata=row.metadata_ or {},
        )

