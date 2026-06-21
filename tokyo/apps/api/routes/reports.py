from datetime import date

from fastapi import APIRouter, Request

from tokyo.apps.api.utils.dependencies import get_runtime
from tokyo.packages.contracts.enums import TradingMode
from tokyo.packages.contracts.reports import DailyReport

reports_router = APIRouter(prefix="/reports", tags=["reports"])


@reports_router.get("/daily", response_model=DailyReport)
async def daily_report(
    request: Request,
    report_date: date,
    trading_mode: TradingMode = TradingMode.paper,
    account_id: str | None = None,
    strategy_id: str | None = None,
) -> DailyReport:
    runtime = get_runtime(request)
    return await runtime.reports.generate(
        report_date=report_date,
        trading_mode=trading_mode,
        account_id=account_id,
        strategy_id=strategy_id,
    )
