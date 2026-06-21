from sqlalchemy import desc, select

from tokyo.packages.contracts.enums import OrderSide, TradingMode
from tokyo.packages.contracts.execution import ExecutionReport
from tokyo.packages.storage.models import ExecutionModel
from tokyo.packages.storage.repositories.base import BaseRepository


class ExecutionRepository(BaseRepository):
    async def add(self, execution: ExecutionReport) -> ExecutionReport:
        self.session.add(
            ExecutionModel(
                execution_id=execution.execution_id,
                broker_execution_id=execution.broker_execution_id,
                order_id=execution.order_id,
                account_id=execution.account_id,
                strategy_id=execution.strategy_id,
                symbol_id=execution.symbol_id,
                trading_mode=execution.trading_mode.value,
                side=execution.side.value,
                quantity=execution.quantity,
                price=execution.price,
                commission=execution.commission,
                commission_asset=execution.commission_asset,
                liquidity=execution.liquidity,
                executed_at=execution.executed_at,
                received_at=execution.received_at,
                metadata_=execution.metadata,
            )
        )
        return execution

    async def list(
        self,
        *,
        account_id: str | None = None,
        strategy_id: str | None = None,
        limit: int = 200,
    ) -> list[ExecutionReport]:
        statement = select(ExecutionModel)
        if account_id:
            statement = statement.where(ExecutionModel.account_id == account_id)
        if strategy_id:
            statement = statement.where(ExecutionModel.strategy_id == strategy_id)
        rows = (
            await self.session.scalars(statement.order_by(desc(ExecutionModel.executed_at)).limit(limit))
        ).all()
        return [self._to_contract(row) for row in rows]

    def _to_contract(self, row: ExecutionModel) -> ExecutionReport:
        return ExecutionReport(
            execution_id=row.execution_id,
            broker_execution_id=row.broker_execution_id,
            order_id=row.order_id,
            account_id=row.account_id,
            strategy_id=row.strategy_id,
            symbol_id=row.symbol_id,
            trading_mode=TradingMode(row.trading_mode),
            side=OrderSide(row.side),
            quantity=row.quantity,
            price=row.price,
            commission=row.commission,
            commission_asset=row.commission_asset,
            liquidity=row.liquidity,
            executed_at=row.executed_at,
            received_at=row.received_at,
            metadata=row.metadata_ or {},
        )

