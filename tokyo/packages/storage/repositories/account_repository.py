from datetime import UTC, datetime

from sqlalchemy import select

from tokyo.packages.contracts.account import Account
from tokyo.packages.contracts.enums import TradingMode, Universe
from tokyo.packages.storage.models import AccountModel
from tokyo.packages.storage.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    async def list(self) -> list[Account]:
        rows = (await self.session.scalars(select(AccountModel).order_by(AccountModel.account_id))).all()
        return [self._to_contract(row) for row in rows]

    async def get(self, account_id: str) -> Account | None:
        row = await self.session.get(AccountModel, account_id)
        return self._to_contract(row) if row else None

    async def upsert(self, account: Account) -> Account:
        now = datetime.now(UTC)
        await self.session.merge(
            AccountModel(
                account_id=account.account_id,
                trading_mode=account.trading_mode.value,
                base_currency=account.base_currency,
                enabled=account.enabled,
                allowed_universes=[item.value for item in account.allowed_universes],
                initial_balances={key: str(value) for key, value in account.initial_balances.items()},
                metadata_=account.metadata,
                created_at=now,
                updated_at=now,
            )
        )
        return account

    def _to_contract(self, row: AccountModel) -> Account:
        return Account(
            account_id=row.account_id,
            trading_mode=TradingMode(row.trading_mode),
            base_currency=row.base_currency,
            enabled=row.enabled,
            allowed_universes=[Universe(item) for item in row.allowed_universes or []],
            initial_balances=row.initial_balances or {},
            metadata=row.metadata_ or {},
        )

