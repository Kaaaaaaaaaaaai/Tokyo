from sqlalchemy import desc, select

from tokyo.packages.contracts.enums import TradingMode
from tokyo.packages.contracts.execution import Position
from tokyo.packages.storage.models import PositionModel
from tokyo.packages.storage.repositories.base import BaseRepository


class PositionRepository(BaseRepository):
    async def add_snapshot(self, position: Position) -> Position:
        self.session.add(
            PositionModel(
                position_id=position.position_id,
                account_id=position.account_id,
                strategy_id=position.strategy_id,
                symbol_id=position.symbol_id,
                trading_mode=position.trading_mode.value,
                quantity=position.quantity,
                average_entry_price=position.average_entry_price,
                mark_price=position.mark_price,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=position.unrealized_pnl,
                source=position.source,
                as_of=position.as_of,
            )
        )
        return position

    async def list_current(self, account_id: str | None = None) -> list[Position]:
        statement = select(PositionModel)
        if account_id:
            statement = statement.where(PositionModel.account_id == account_id)
        rows = (
            await self.session.scalars(statement.order_by(desc(PositionModel.as_of)).limit(500))
        ).all()
        seen: set[tuple[str, str, str | None]] = set()
        positions: list[Position] = []
        for row in rows:
            key = (row.account_id, row.symbol_id, row.strategy_id)
            if key in seen:
                continue
            seen.add(key)
            positions.append(self._to_contract(row))
        return positions

    def _to_contract(self, row: PositionModel) -> Position:
        return Position(
            position_id=row.position_id,
            account_id=row.account_id,
            strategy_id=row.strategy_id,
            symbol_id=row.symbol_id,
            trading_mode=TradingMode(row.trading_mode),
            quantity=row.quantity,
            average_entry_price=row.average_entry_price,
            mark_price=row.mark_price,
            realized_pnl=row.realized_pnl,
            unrealized_pnl=row.unrealized_pnl,
            source=row.source,
            as_of=row.as_of,
        )

