import uuid

import pytest

from app.core.config import Settings
from app.modules.jobs.domain import JobStatus, SourceStatus, TransitionType
from app.modules.jobs.errors import QueueFullError
from app.modules.jobs.queue import JobQueue
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore
from app.modules.storage.service import StorageService


@pytest.mark.asyncio
async def test_source_status_flow(session_factory) -> None:
    service = JobStoreService(session_factory)
    store = JobStore(service)

    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert source.status == SourceStatus.DOWNLOADING

    ready = await service.mark_source_ready(
        source.id,
        duration=120.0,
        title="Test",
        path="/media/source.mp4",
    )
    assert ready.status == SourceStatus.READY
    assert ready.duration == 120.0

    errored = await service.mark_source_error(source.id, error="download failed")
    assert errored.status == SourceStatus.ERROR
    assert errored.error == "download failed"


@pytest.mark.asyncio
async def test_job_status_flow(session_factory) -> None:
    service = JobStoreService(session_factory)
    store = JobStore(service)

    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    await service.mark_source_ready(
        source.id,
        duration=60.0,
        title="Test",
        path="/media/source.mp4",
    )

    job = await store.create_job(
        source.id,
        [{"start": 0.0, "end": 10.0}],
        TransitionType.FADE,
        0.5,
    )
    assert job.status == JobStatus.QUEUED

    processing = await store.mark_job_processing(job.id)
    assert processing.status == JobStatus.PROCESSING

    done = await service.mark_job_done(job.id, "/media/result.mp4")
    assert done.status == JobStatus.DONE
    assert done.result_path == "/media/result.mp4"


@pytest.mark.asyncio
async def test_queue_full_raises(fake_redis) -> None:
    settings = Settings(queue_size=2, arq_queue_key="arq:queue")
    queue = JobQueue(fake_redis, settings=settings)

    await fake_redis.zadd("arq:queue", {"job-1": 1, "job-2": 2})

    assert await queue.depth() == 2

    with pytest.raises(QueueFullError):
        await queue.check_capacity()


@pytest.mark.asyncio
async def test_queue_below_limit_ok(fake_redis) -> None:
    settings = Settings(queue_size=2, arq_queue_key="arq:queue")
    queue = JobQueue(fake_redis, settings=settings)

    await fake_redis.zadd("arq:queue", {"job-1": 1})
    await queue.check_capacity()


def test_storage_job_dir_cleanup(tmp_path) -> None:
    settings = Settings(work_dir=str(tmp_path / "work"))
    storage = StorageService(settings=settings)

    job_id = str(uuid.uuid4())
    job_dir = storage.job_dir(job_id)
    assert job_dir.is_dir()

    storage.cleanup(job_id)
    assert not job_dir.exists()
