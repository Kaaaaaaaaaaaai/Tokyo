from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, select

from tokyo.packages.contracts.enums import OrderSide, OrderStatus, OrderType, TimeInForce, TradingMode
from tokyo.packages.contracts.orders import Order, OrderEvent
from tokyo.packages.storage.models import OrderEventModel, OrderModel
from tokyo.packages.storage.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    async def create(self, order: Order) -> Order:
        self.session.add(self._to_model(order))
        return order

    async def get(self, order_id: UUID) -> Order | None:
        row = await self.session.get(OrderModel, order_id)
        return self._to_contract(row) if row else None

    async def find_by_client_order_id(
        self,
        *,
        strategy_id: str,
        account_id: str,
        trading_mode: TradingMode,
        client_order_id: str,
    ) -> Order | None:
        row = await self.session.scalar(
            select(OrderModel).where(
                OrderModel.strategy_id == strategy_id,
                OrderModel.account_id == account_id,
                OrderModel.trading_mode == trading_mode.value,
                OrderModel.client_order_id == client_order_id,
            )
        )
        return self._to_contract(row) if row else None

    async def list(
        self,
        *,
        strategy_id: str | None = None,
        account_id: str | None = None,
        status: OrderStatus | None = None,
        limit: int = 200,
    ) -> list[Order]:
        statement = select(OrderModel)
        if strategy_id:
            statement = statement.where(OrderModel.strategy_id == strategy_id)
        if account_id:
            statement = statement.where(OrderModel.account_id == account_id)
        if status:
            statement = statement.where(OrderModel.status == status.value)
        rows = (
            await self.session.scalars(statement.order_by(desc(OrderModel.created_at)).limit(limit))
        ).all()
        return [self._to_contract(row) for row in rows]

    async def update_status(
        self,
        order_id: UUID,
        status: OrderStatus,
        updated_at: datetime,
        filled_quantity: str | None = None,
        broker_order_id: str | None = None,
    ) -> Order | None:
        row = await self.session.get(OrderModel, order_id)
        if row is None:
            return None
        row.status = status.value
        row.updated_at = updated_at
        if filled_quantity is not None:
            row.filled_quantity = filled_quantity
        if broker_order_id is not None:
            row.broker_order_id = broker_order_id
        return self._to_contract(row)

    async def add_event(self, event: OrderEvent) -> OrderEvent:
        self.session.add(
            OrderEventModel(
                event_id=event.event_id,
                order_id=event.order_id,
                event_type=event.event_type,
                previous_status=event.previous_status.value if event.previous_status else None,
                new_status=event.new_status.value,
                reason_code=event.reason_code,
                message=event.message,
                payload=event.payload,
                correlation_id=event.correlation_id,
                created_at=event.created_at,
            )
        )
        return event

    async def events_for_order(self, order_id: UUID) -> list[OrderEvent]:
        rows = (
            await self.session.scalars(
                select(OrderEventModel)
                .where(OrderEventModel.order_id == order_id)
                .order_by(OrderEventModel.created_at)
            )
        ).all()
        return [self._event_to_contract(row) for row in rows]

    def _to_model(self, order: Order) -> OrderModel:
        return OrderModel(
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            strategy_id=order.strategy_id,
            account_id=order.account_id,
            trading_mode=order.trading_mode.value,
            symbol_id=order.symbol_id,
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            time_in_force=order.time_in_force.value,
            status=order.status.value,
            adapter_id=order.adapter_id,
            broker_order_id=order.broker_order_id,
            correlation_id=order.correlation_id,
            metadata_=order.metadata,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def _to_contract(self, row: OrderModel) -> Order:
        return Order(
            order_id=row.order_id,
            client_order_id=row.client_order_id,
            strategy_id=row.strategy_id,
            account_id=row.account_id,
            trading_mode=TradingMode(row.trading_mode),
            symbol_id=row.symbol_id,
            side=OrderSide(row.side),
            order_type=OrderType(row.order_type),
            quantity=row.quantity,
            filled_quantity=row.filled_quantity,
            limit_price=row.limit_price,
            stop_price=row.stop_price,
            time_in_force=TimeInForce(row.time_in_force),
            status=OrderStatus(row.status),
            adapter_id=row.adapter_id,
            broker_order_id=row.broker_order_id,
            correlation_id=row.correlation_id,
            metadata=row.metadata_ or {},
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _event_to_contract(self, row: OrderEventModel) -> OrderEvent:
        return OrderEvent(
            event_id=row.event_id,
            order_id=row.order_id,
            event_type=row.event_type,
            previous_status=OrderStatus(row.previous_status) if row.previous_status else None,
            new_status=OrderStatus(row.new_status),
            reason_code=row.reason_code,
            message=row.message,
            payload=row.payload or {},
            correlation_id=row.correlation_id,
            created_at=row.created_at,
        )

