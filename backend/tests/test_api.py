import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.deps import get_dispatcher, get_job_queue, get_job_store
from app.main import app
from app.modules.jobs.domain import JobStatus, SourceStatus
from app.modules.jobs.queue import JobQueue
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore


class FakeDispatcher:
    async def dispatch_source_download(self, source_id: uuid.UUID, url: str) -> None:
        return None

    async def dispatch_render(self, job_id: uuid.UUID) -> None:
        return None


@pytest.fixture
async def api_client(session_factory, fake_redis):
    store = JobStore(JobStoreService(session_factory))
    settings = Settings(queue_size=10, arq_queue_key="arq:queue")
    queue = JobQueue(fake_redis, settings=settings)

    app.dependency_overrides[get_job_store] = lambda: store
    app.dependency_overrides[get_job_queue] = lambda: queue
    app.dependency_overrides[get_dispatcher] = lambda: FakeDispatcher()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, store

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_source_returns_id(api_client) -> None:
    client, _store = api_client
    response = await client.post(
        "/api/sources",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == SourceStatus.DOWNLOADING
    assert "source_id" in body


@pytest.mark.asyncio
async def test_create_source_rejects_invalid_url(api_client) -> None:
    client, _store = api_client
    response = await client.post(
        "/api/sources",
        json={"url": "https://example.com/not-youtube"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_source(api_client) -> None:
    client, store = api_client
    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    response = await client.get(f"/api/sources/{source.id}")
    assert response.status_code == 200
    assert response.json()["status"] == SourceStatus.DOWNLOADING


@pytest.mark.asyncio
async def test_create_job_validation_empty_clips(api_client) -> None:
    client, store = api_client
    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    service = JobStoreService(store._service._session_factory)
    await service.mark_source_ready(
        source.id,
        duration=60.0,
        title="Test",
        path="/tmp/source.mp4",
    )
    response = await client.post(
        "/api/jobs",
        json={
            "source_id": str(source.id),
            "clips": [],
            "transition": "cut",
            "transition_duration": 0,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_source_not_ready(api_client) -> None:
    client, store = api_client
    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    response = await client.post(
        "/api/jobs",
        json={
            "source_id": str(source.id),
            "clips": [{"start": 0, "end": 5}],
            "transition": "cut",
            "transition_duration": 0,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "source not ready"


@pytest.mark.asyncio
async def test_create_job_success(api_client) -> None:
    client, store = api_client
    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    service = JobStoreService(store._service._session_factory)
    await service.mark_source_ready(
        source.id,
        duration=60.0,
        title="Test",
        path="/tmp/source.mp4",
    )
    response = await client.post(
        "/api/jobs",
        json={
            "source_id": str(source.id),
            "clips": [{"start": 0, "end": 5}, {"start": 10, "end": 15}],
            "transition": "fade",
            "transition_duration": 0.5,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == JobStatus.QUEUED
    assert "job_id" in body


@pytest.mark.asyncio
async def test_create_job_queue_full(api_client, fake_redis, monkeypatch) -> None:
    client, store = api_client
    settings = Settings(queue_size=1, arq_queue_key="arq:queue")
    queue = JobQueue(fake_redis, settings=settings)
    await fake_redis.zadd("arq:queue", {"job-1": 1})

    app.dependency_overrides[get_job_queue] = lambda: queue

    source = await store.create_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    service = JobStoreService(store._service._session_factory)
    await service.mark_source_ready(
        source.id,
        duration=60.0,
        title="Test",
        path="/tmp/source.mp4",
    )
    response = await client.post(
        "/api/jobs",
        json={
            "source_id": str(source.id),
            "clips": [{"start": 0, "end": 5}],
            "transition": "cut",
            "transition_duration": 0,
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "queue full"
