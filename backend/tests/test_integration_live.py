import httpx
import pytest
from sqlalchemy import text

from app.core.database import close_database, get_session_factory, init_database
from app.core.redis import close_redis, init_redis
from app.modules.jobs.domain import JobStatus, SourceStatus, TransitionType
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_live_postgres_source_and_job_flow() -> None:
    await init_database()
    await init_redis()
    try:
        session_factory = get_session_factory()
        service = JobStoreService(session_factory)
        store = JobStore(service)

        source = await store.create_source(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        assert source.status == SourceStatus.DOWNLOADING

        ready = await service.mark_source_ready(
            source.id,
            duration=90.0,
            title="Integration",
            path="/media/test/source.mp4",
        )
        assert ready.status == SourceStatus.READY

        job = await store.create_job(
            source.id,
            [{"start": 0.0, "end": 10.0}],
            TransitionType.CUT,
            0.0,
        )
        assert job.status == JobStatus.QUEUED

        async with session_factory() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM sources"))
            source_count = result.scalar_one()
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            job_count = result.scalar_one()

        assert source_count >= 1
        assert job_count >= 1
    finally:
        await close_redis()
        await close_database()


@pytest.mark.asyncio
async def test_live_api_health_endpoint() -> None:
    base_url = "http://127.0.0.1:8000"
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
