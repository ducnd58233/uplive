import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.domain import SourceRecord, SourceStatus
from app.modules.jobs.models.source_row import SourceRow


def _to_record(row: SourceRow) -> SourceRecord:
    return SourceRecord(
        id=row.id,
        url=row.url,
        status=SourceStatus(row.status),
        duration=row.duration,
        title=row.title,
        path=row.path,
        error=row.error,
        created_at=row.created_at,
    )


class SourceRepository:
    async def create(
        self,
        session: AsyncSession,
        url: str,
        status: SourceStatus,
    ) -> SourceRecord:
        row = SourceRow(url=url, status=status.value)
        session.add(row)
        await session.flush()
        return _to_record(row)

    async def get_by_id(
        self,
        session: AsyncSession,
        source_id: uuid.UUID,
    ) -> SourceRecord | None:
        row = await session.get(SourceRow, source_id)
        if row is None:
            return None
        return _to_record(row)

    async def update_status(
        self,
        session: AsyncSession,
        source_id: uuid.UUID,
        status: SourceStatus,
        duration: float | None = None,
        title: str | None = None,
        path: str | None = None,
        error: str | None = None,
    ) -> SourceRecord | None:
        row = await session.get(SourceRow, source_id)
        if row is None:
            return None
        row.status = status.value
        if duration is not None:
            row.duration = duration
        if title is not None:
            row.title = title
        if path is not None:
            row.path = path
        if error is not None:
            row.error = error
        await session.flush()
        return _to_record(row)

    async def list_by_status(
        self,
        session: AsyncSession,
        status: SourceStatus,
    ) -> list[SourceRecord]:
        result = await session.execute(
            select(SourceRow).where(SourceRow.status == status.value)
        )
        return [_to_record(row) for row in result.scalars().all()]
