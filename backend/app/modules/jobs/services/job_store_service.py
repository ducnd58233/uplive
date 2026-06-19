import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.jobs.domain import (
    JobRecord,
    JobStatus,
    SourceRecord,
    SourceStatus,
    TransitionType,
)
from app.modules.jobs.errors import JobNotFoundError, SourceNotFoundError
from app.modules.jobs.repositories.job_repository import JobRepository
from app.modules.jobs.repositories.source_repository import SourceRepository


class JobStoreService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        source_repository: SourceRepository | None = None,
        job_repository: JobRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._source_repository = source_repository or SourceRepository()
        self._job_repository = job_repository or JobRepository()

    async def create_source(self, url: str) -> SourceRecord:
        async with self._session_factory() as session, session.begin():
            return await self._source_repository.create(
                session,
                url=url,
                status=SourceStatus.DOWNLOADING,
            )

    async def get_source(self, source_id: uuid.UUID) -> SourceRecord | None:
        async with self._session_factory() as session, session.begin():
            return await self._source_repository.get_by_id(session, source_id)

    async def mark_source_ready(
        self,
        source_id: uuid.UUID,
        duration: float,
        title: str,
        path: str,
    ) -> SourceRecord:
        async with self._session_factory() as session, session.begin():
            record = await self._source_repository.update_status(
                session,
                source_id,
                SourceStatus.READY,
                duration=duration,
                title=title,
                path=path,
            )
            if record is None:
                raise SourceNotFoundError(str(source_id))
            return record

    async def mark_source_error(
        self,
        source_id: uuid.UUID,
        error: str,
    ) -> SourceRecord:
        async with self._session_factory() as session, session.begin():
            record = await self._source_repository.update_status(
                session,
                source_id,
                SourceStatus.ERROR,
                error=error,
            )
            if record is None:
                raise SourceNotFoundError(str(source_id))
            return record

    async def create_job(
        self,
        source_id: uuid.UUID,
        clips: list[dict[str, float]],
        transition: TransitionType,
        transition_duration: float,
    ) -> JobRecord:
        async with self._session_factory() as session, session.begin():
            source = await self._source_repository.get_by_id(session, source_id)
            if source is None:
                raise SourceNotFoundError(str(source_id))
            return await self._job_repository.create(
                session,
                source_id=source_id,
                clips=clips,
                transition=transition,
                transition_duration=transition_duration,
                status=JobStatus.QUEUED,
            )

    async def get_job(self, job_id: uuid.UUID) -> JobRecord | None:
        async with self._session_factory() as session, session.begin():
            return await self._job_repository.get_by_id(session, job_id)

    async def mark_job_processing(self, job_id: uuid.UUID) -> JobRecord:
        return await self._transition_job(
            job_id,
            JobStatus.PROCESSING,
            progress=0,
        )

    async def mark_job_done(
        self,
        job_id: uuid.UUID,
        result_path: str,
    ) -> JobRecord:
        return await self._transition_job(
            job_id,
            JobStatus.DONE,
            progress=100,
            result_path=result_path,
        )

    async def mark_job_error(self, job_id: uuid.UUID, error: str) -> JobRecord:
        return await self._transition_job(job_id, JobStatus.ERROR, error=error)

    async def count_queued_jobs(self) -> int:
        async with self._session_factory() as session, session.begin():
            return await self._job_repository.count_by_status(
                session,
                JobStatus.QUEUED,
            )

    async def _transition_job(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        progress: int | None = None,
        result_path: str | None = None,
        error: str | None = None,
    ) -> JobRecord:
        async with self._session_factory() as session, session.begin():
            record = await self._job_repository.update_status(
                session,
                job_id,
                status,
                progress=progress,
                result_path=result_path,
                error=error,
            )
            if record is None:
                raise JobNotFoundError(str(job_id))
            return record
