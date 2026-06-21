from datetime import UTC, datetime

from sqlalchemy import select

from tokyo.packages.contracts.enums import SymbolStatus, Universe, Variant
from tokyo.packages.contracts.symbol import Symbol
from tokyo.packages.storage.models import SymbolModel
from tokyo.packages.storage.repositories.base import BaseRepository


class SymbolRepository(BaseRepository):
    async def list(self) -> list[Symbol]:
        rows = (await self.session.scalars(select(SymbolModel).order_by(SymbolModel.symbol))).all()
        return [self._to_contract(row) for row in rows]

    async def get(self, symbol_id: str) -> Symbol | None:
        row = await self.session.get(SymbolModel, symbol_id)
        return self._to_contract(row) if row else None

    async def upsert(self, symbol: Symbol) -> Symbol:
        now = datetime.now(UTC)
        row = SymbolModel(
            symbol_id=symbol.symbol_id,
            symbol_uid=symbol.symbol_uid,
            symbol=symbol.symbol,
            universe=symbol.universe.value,
            variant=symbol.variant.value,
            asset=symbol.asset,
            quote_asset=symbol.quote_asset,
            unit=symbol.unit,
            price_precision=symbol.price_precision,
            quantity_precision=symbol.quantity_precision,
            min_quantity=symbol.min_quantity,
            min_notional=symbol.min_notional,
            tick_size=symbol.tick_size,
            lot_size=symbol.lot_size,
            status=symbol.status.value,
            valid_from=symbol.valid_from,
            valid_to=symbol.valid_to,
            metadata_=symbol.metadata,
            created_at=now,
            updated_at=now,
        )
        await self.session.merge(row)
        return symbol

    def _to_contract(self, row: SymbolModel) -> Symbol:
        return Symbol(
            symbol_id=row.symbol_id,
            symbol_uid=row.symbol_uid,
            symbol=row.symbol,
            universe=Universe(row.universe),
            variant=Variant(row.variant),
            asset=row.asset,
            quote_asset=row.quote_asset,
            unit=row.unit,
            price_precision=row.price_precision,
            quantity_precision=row.quantity_precision,
            min_quantity=row.min_quantity,
            min_notional=row.min_notional,
            tick_size=row.tick_size,
            lot_size=row.lot_size,
            status=SymbolStatus(row.status),
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            metadata=row.metadata_ or {},
        )

