import uuid
from pathlib import Path

import pytest

from app.core.config import Settings
from app.modules.editor.ffmpeg import make_test_clip
from app.modules.editor.service import EditorService
from app.modules.jobs.domain import JobStatus, SourceStatus, TransitionType
from app.modules.jobs.errors import JobNotFoundError
from app.modules.jobs.pipeline import JobPipeline
from app.modules.jobs.progress import JobProgressStore
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore
from app.modules.sources.errors import DownloadError
from app.modules.sources.service import FetchedSource
from app.modules.storage.service import StorageService


class FakeSourceService:
    def __init__(
        self,
        result: FetchedSource | None = None,
        error: Exception | None = None,
    ):
        self._result = result
        self._error = error

    def download_source(self, source_id: str, url: str) -> FetchedSource:
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise DownloadError("missing fake result")
        return self._result


class FailingEditorService(EditorService):
    def __init__(self, message: str = "render failed") -> None:
        super().__init__()
        self._message = message

    def extract(
        self,
        input_path: Path,
        output_path: Path,
        start: float,
        end: float,
    ) -> None:
        raise RuntimeError(self._message)


@pytest.fixture
def pipeline_deps(session_factory, fake_redis, tmp_path):
    settings = Settings(work_dir=str(tmp_path / "work"))
    storage = StorageService(settings=settings)
    job_store = JobStore(JobStoreService(session_factory))
    progress_store = JobProgressStore(fake_redis, settings=settings)
    return {
        "settings": settings,
        "storage": storage,
        "job_store": job_store,
        "progress_store": progress_store,
    }


@pytest.mark.asyncio
async def test_run_source_download_marks_ready(pipeline_deps) -> None:
    fetched = FetchedSource(path="/media/source.mp4", duration=42.0, title="Demo")
    pipeline = JobPipeline(
        pipeline_deps["job_store"],
        pipeline_deps["progress_store"],
        source_service=FakeSourceService(result=fetched),
        storage=pipeline_deps["storage"],
        settings=pipeline_deps["settings"],
    )

    source = await pipeline_deps["job_store"].create_source(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    await pipeline.run_source_download(source.id, source.url)

    updated = await pipeline_deps["job_store"].get_source(source.id)
    assert updated is not None
    assert updated.status == SourceStatus.READY
    assert updated.duration == 42.0
    assert updated.title == "Demo"


@pytest.mark.asyncio
async def test_run_source_download_cleans_up_on_failure(pipeline_deps) -> None:
    pipeline = JobPipeline(
        pipeline_deps["job_store"],
        pipeline_deps["progress_store"],
        source_service=FakeSourceService(error=DownloadError("network down")),
        storage=pipeline_deps["storage"],
        settings=pipeline_deps["settings"],
    )

    source = await pipeline_deps["job_store"].create_source(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    pipeline_deps["storage"].job_dir(str(source.id))
    with pytest.raises(DownloadError):
        await pipeline.run_source_download(source.id, source.url)

    updated = await pipeline_deps["job_store"].get_source(source.id)
    assert updated is not None
    assert updated.status == SourceStatus.ERROR
    assert not (pipeline_deps["storage"].root / str(source.id)).exists()


@pytest.mark.asyncio
async def test_run_job_render_reaches_done_with_result(pipeline_deps) -> None:
    storage: StorageService = pipeline_deps["storage"]
    job_store: JobStore = pipeline_deps["job_store"]
    source_id = uuid.uuid4()
    source_path = storage.source_path(str(source_id))
    make_test_clip(source_path, duration=4.0)

    source = await job_store.create_source(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    await job_store.mark_source_ready(
        source.id,
        duration=4.0,
        title="Test clip",
        path=str(source_path),
    )

    job = await job_store.create_job(
        source.id,
        [{"start": 0.0, "end": 1.5}, {"start": 1.5, "end": 3.0}],
        TransitionType.CUT,
        0.0,
    )

    pipeline = JobPipeline(
        job_store,
        pipeline_deps["progress_store"],
        storage=storage,
        settings=pipeline_deps["settings"],
    )
    await pipeline.run_job_render(job.id)

    done = await job_store.get_job(job.id)
    assert done is not None
    assert done.status == JobStatus.DONE
    assert done.progress == 100
    assert done.result_path is not None
    assert Path(done.result_path).exists()

    redis_progress = await pipeline_deps["progress_store"].read(job.id)
    assert redis_progress == 100


@pytest.mark.asyncio
async def test_run_job_render_cleans_up_on_failure(pipeline_deps) -> None:
    storage: StorageService = pipeline_deps["storage"]
    job_store: JobStore = pipeline_deps["job_store"]
    source_id = uuid.uuid4()
    source_path = storage.source_path(str(source_id))
    make_test_clip(source_path, duration=3.0)

    source = await job_store.create_source(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    await job_store.mark_source_ready(
        source.id,
        duration=3.0,
        title="Test clip",
        path=str(source_path),
    )

    job = await job_store.create_job(
        source.id,
        [{"start": 0.0, "end": 1.0}],
        TransitionType.CUT,
        0.0,
    )

    pipeline = JobPipeline(
        job_store,
        pipeline_deps["progress_store"],
        editor_service=FailingEditorService(),
        storage=storage,
        settings=pipeline_deps["settings"],
    )

    with pytest.raises(RuntimeError, match="render failed"):
        await pipeline.run_job_render(job.id)

    failed = await job_store.get_job(job.id)
    assert failed is not None
    assert failed.status == JobStatus.ERROR
    assert not (storage.root / str(job.id)).exists()


@pytest.mark.asyncio
async def test_run_job_render_missing_job_raises(pipeline_deps) -> None:
    pipeline = JobPipeline(
        pipeline_deps["job_store"],
        pipeline_deps["progress_store"],
        storage=pipeline_deps["storage"],
        settings=pipeline_deps["settings"],
    )

    missing_id = uuid.uuid4()
    with pytest.raises(JobNotFoundError):
        await pipeline.run_job_render(missing_id)
