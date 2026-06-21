from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from tokyo.packages.contracts.enums import BackfillStatus
from tokyo.packages.contracts.market_data import BackfillJob, BackfillRequest
from tokyo.packages.storage.models import BackfillJobModel
from tokyo.packages.storage.repositories.base import BaseRepository


class BackfillRepository(BaseRepository):
    async def create(self, request: BackfillRequest) -> BackfillJob:
        job = BackfillJob(request=request, status=BackfillStatus.requested)
        self.session.add(
            BackfillJobModel(
                job_id=job.job_id,
                request=request.model_dump(mode="json"),
                status=job.status.value,
                rows_fetched=0,
                rows_accepted=0,
                rows_rejected=0,
                gaps_found=0,
                started_at=None,
                finished_at=None,
                error_details={},
                created_at=datetime.now(UTC),
            )
        )
        return job

    async def get(self, job_id: UUID) -> BackfillJob | None:
        row = await self.session.get(BackfillJobModel, job_id)
        if row is None:
            return None
        return BackfillJob(
            job_id=row.job_id,
            request=BackfillRequest.model_validate(row.request),
            status=BackfillStatus(row.status),
            rows_fetched=row.rows_fetched,
            rows_accepted=row.rows_accepted,
            rows_rejected=row.rows_rejected,
            gaps_found=row.gaps_found,
            started_at=row.started_at,
            finished_at=row.finished_at,
            error_details=row.error_details or {},
        )

    async def list(self, limit: int = 100) -> list[BackfillJob]:
        rows = (
            await self.session.scalars(
                select(BackfillJobModel).order_by(BackfillJobModel.created_at).limit(limit)
            )
        ).all()
        return [
            BackfillJob(
                job_id=row.job_id,
                request=BackfillRequest.model_validate(row.request),
                status=BackfillStatus(row.status),
                rows_fetched=row.rows_fetched,
                rows_accepted=row.rows_accepted,
                rows_rejected=row.rows_rejected,
                gaps_found=row.gaps_found,
                started_at=row.started_at,
                finished_at=row.finished_at,
                error_details=row.error_details or {},
            )
            for row in rows
        ]

