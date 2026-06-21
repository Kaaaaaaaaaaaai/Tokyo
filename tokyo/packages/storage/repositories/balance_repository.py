from sqlalchemy import desc, select

from tokyo.packages.contracts.execution import Balance
from tokyo.packages.storage.models import BalanceModel
from tokyo.packages.storage.repositories.base import BaseRepository


class BalanceRepository(BaseRepository):
    async def add_snapshot(self, balance: Balance) -> Balance:
        self.session.add(
            BalanceModel(
                balance_id=balance.balance_id,
                account_id=balance.account_id,
                asset=balance.asset,
                available=balance.available,
                locked=balance.locked,
                total=balance.total,
                source=balance.source,
                as_of=balance.as_of,
            )
        )
        return balance

    async def list_current(self, account_id: str | None = None) -> list[Balance]:
        statement = select(BalanceModel)
        if account_id:
            statement = statement.where(BalanceModel.account_id == account_id)
        rows = (await self.session.scalars(statement.order_by(desc(BalanceModel.as_of)).limit(500))).all()
        seen: set[tuple[str, str]] = set()
        balances: list[Balance] = []
        for row in rows:
            key = (row.account_id, row.asset)
            if key in seen:
                continue
            seen.add(key)
            balances.append(
                Balance(
                    balance_id=row.balance_id,
                    account_id=row.account_id,
                    asset=row.asset,
                    available=row.available,
                    locked=row.locked,
                    total=row.total,
                    source=row.source,
                    as_of=row.as_of,
                )
            )
        return balances

