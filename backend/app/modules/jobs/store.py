import uuid

from app.modules.jobs.domain import JobRecord, SourceRecord, TransitionType
from app.modules.jobs.services.job_store_service import JobStoreService


class JobStore:
    def __init__(self, service: JobStoreService) -> None:
        self._service = service

    async def create_source(self, url: str) -> SourceRecord:
        return await self._service.create_source(url)

    async def get_source(self, source_id: uuid.UUID) -> SourceRecord | None:
        return await self._service.get_source(source_id)

    async def create_job(
        self,
        source_id: uuid.UUID,
        clips: list[dict[str, float]],
        transition: TransitionType,
        transition_duration: float,
    ) -> JobRecord:
        return await self._service.create_job(
            source_id,
            clips,
            transition,
            transition_duration,
        )

    async def get_job(self, job_id: uuid.UUID) -> JobRecord | None:
        return await self._service.get_job(job_id)

    async def mark_job_processing(self, job_id: uuid.UUID) -> JobRecord:
        return await self._service.mark_job_processing(job_id)

    async def mark_job_done(self, job_id: uuid.UUID, result_path: str) -> JobRecord:
        return await self._service.mark_job_done(job_id, result_path)

    async def mark_job_error(self, job_id: uuid.UUID, error: str) -> JobRecord:
        return await self._service.mark_job_error(job_id, error)

    async def update_job_progress(self, job_id: uuid.UUID, progress: int) -> JobRecord:
        return await self._service.update_job_progress(job_id, progress)

    async def mark_source_ready(
        self,
        source_id: uuid.UUID,
        duration: float,
        title: str,
        path: str,
    ) -> SourceRecord:
        return await self._service.mark_source_ready(
            source_id,
            duration,
            title,
            path,
        )

    async def mark_source_error(
        self,
        source_id: uuid.UUID,
        error: str,
    ) -> SourceRecord:
        return await self._service.mark_source_error(source_id, error)

    async def count_queued_jobs(self) -> int:
        return await self._service.count_queued_jobs()
