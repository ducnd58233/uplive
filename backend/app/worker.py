from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def startup(ctx: dict) -> None:
    configure_logging()
    logger.info("Worker process started")
    _ = ctx


async def shutdown(ctx: dict) -> None:
    logger.info("Worker process stopped")
    _ = ctx


class WorkerSettings:
    functions: list = []
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1
    job_timeout = 3600
    on_startup = startup
    on_shutdown = shutdown
