from sqlalchemy.ext.asyncio import AsyncSession

from tokyo.packages.common.config import ConfigBundle
from tokyo.packages.storage.repositories.account_repository import AccountRepository
from tokyo.packages.storage.repositories.risk_repository import RiskRepository
from tokyo.packages.storage.repositories.strategy_repository import StrategyRepository
from tokyo.packages.storage.repositories.symbol_repository import SymbolRepository


class ConfigSeeder:
    """Seeds validated YAML config into durable storage."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed(self, bundle: ConfigBundle) -> None:
        symbols = SymbolRepository(self._session)
        accounts = AccountRepository(self._session)
        strategies = StrategyRepository(self._session)
        risks = RiskRepository(self._session)
        for symbol in bundle.symbols:
            await symbols.upsert(symbol)
        for account in bundle.accounts:
            await accounts.upsert(account)
        for strategy in bundle.strategies:
            await strategies.upsert(strategy)
        for risk_limit in bundle.risk_limits:
            await risks.upsert_limit(risk_limit)

