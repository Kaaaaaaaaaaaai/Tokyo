from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from tokyo.packages.storage.models import IdempotencyKeyModel
from tokyo.packages.storage.repositories.base import BaseRepository


class IdempotencyRepository(BaseRepository):
    async def get(self, *, key: str, route: str, actor_id: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(IdempotencyKeyModel).where(
                IdempotencyKeyModel.key == key,
                IdempotencyKeyModel.route == route,
                IdempotencyKeyModel.actor_id == actor_id,
            )
        )
        return row.response_payload if row else None

    async def record(
        self,
        *,
        key: str,
        route: str,
        actor_id: str,
        request_hash: str,
        response_payload: dict[str, Any],
    ) -> None:
        self.session.add(
            IdempotencyKeyModel(
                id=uuid4(),
                key=key,
                route=route,
                actor_id=actor_id,
                request_hash=request_hash,
                response_payload=response_payload,
                created_at=datetime.now(UTC),
            )
        )

