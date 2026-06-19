import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.domain import JobRecord, JobStatus, TransitionType
from app.modules.jobs.models.job_row import JobRow


def _to_record(row: JobRow) -> JobRecord:
    return JobRecord(
        id=row.id,
        source_id=row.source_id,
        clips=row.clips,
        transition=TransitionType(row.transition),
        transition_duration=row.transition_duration,
        status=JobStatus(row.status),
        progress=row.progress,
        result_path=row.result_path,
        error=row.error,
        created_at=row.created_at,
    )


class JobRepository:
    async def create(
        self,
        session: AsyncSession,
        source_id: uuid.UUID,
        clips: list[dict[str, float]],
        transition: TransitionType,
        transition_duration: float,
        status: JobStatus,
    ) -> JobRecord:
        row = JobRow(
            source_id=source_id,
            clips=clips,
            transition=transition.value,
            transition_duration=transition_duration,
            status=status.value,
        )
        session.add(row)
        await session.flush()
        return _to_record(row)

    async def get_by_id(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> JobRecord | None:
        row = await session.get(JobRow, job_id)
        if row is None:
            return None
        return _to_record(row)

    async def update_progress(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        progress: int,
    ) -> JobRecord | None:
        row = await session.get(JobRow, job_id)
        if row is None:
            return None
        row.progress = progress
        await session.flush()
        return _to_record(row)

    async def update_status(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        status: JobStatus,
        progress: int | None = None,
        result_path: str | None = None,
        error: str | None = None,
    ) -> JobRecord | None:
        row = await session.get(JobRow, job_id)
        if row is None:
            return None
        row.status = status.value
        if progress is not None:
            row.progress = progress
        if result_path is not None:
            row.result_path = result_path
        if error is not None:
            row.error = error
        await session.flush()
        return _to_record(row)

    async def count_by_status(
        self,
        session: AsyncSession,
        status: JobStatus,
    ) -> int:
        result = await session.execute(
            select(func.count())
            .select_from(JobRow)
            .where(JobRow.status == status.value)
        )
        return int(result.scalar_one())
