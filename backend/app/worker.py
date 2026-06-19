import uuid

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.database import close_database, get_session_factory, init_database
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis, init_redis
from app.modules.editor.service import EditorService
from app.modules.jobs.pipeline import JobPipeline
from app.modules.jobs.progress import JobProgressStore
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore
from app.modules.sources.service import SourceService
from app.modules.storage.service import StorageService

logger = get_logger(__name__)


def build_pipeline(ctx: dict) -> JobPipeline:
    return JobPipeline(
        ctx["job_store"],
        ctx["progress_store"],
        source_service=SourceService(storage=ctx["storage"]),
        editor_service=EditorService(),
        storage=ctx["storage"],
        settings=ctx["settings"],
    )


async def startup(ctx: dict) -> None:
    setup_logging()
    settings = get_settings()
    await init_database(settings)
    redis = await init_redis(settings)
    session_factory = get_session_factory()
    storage = StorageService(settings)
    ctx["settings"] = settings
    ctx["storage"] = storage
    ctx["job_store"] = JobStore(JobStoreService(session_factory))
    ctx["progress_store"] = JobProgressStore(redis, settings)
    ctx["pipeline"] = build_pipeline(ctx)
    logger.info("worker started")


async def shutdown(ctx: dict) -> None:
    await close_redis()
    await close_database()
    logger.info("worker stopped")


async def download_source(ctx: dict, source_id: str, url: str) -> None:
    pipeline: JobPipeline = ctx["pipeline"]
    await pipeline.run_source_download(uuid.UUID(source_id), url)


async def render_job(ctx: dict, job_id: str) -> None:
    pipeline: JobPipeline = ctx["pipeline"]
    await pipeline.run_job_render(uuid.UUID(job_id))


class WorkerSettings:
    functions = [download_source, render_job]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1
    job_timeout = 3600
    on_startup = startup
    on_shutdown = shutdown
