from arq import ArqRedis
from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.database import get_session_factory
from app.core.redis import get_redis_client
from app.modules.jobs.dispatcher import JobDispatcher
from app.modules.jobs.progress import JobProgressStore
from app.modules.jobs.queue import JobQueue
from app.modules.jobs.services.job_store_service import JobStoreService
from app.modules.jobs.store import JobStore
from app.modules.storage.service import StorageService


def get_settings_dep() -> Settings:
    return get_settings()


def get_job_store() -> JobStore:
    return JobStore(JobStoreService(get_session_factory()))


def get_job_queue() -> JobQueue:
    return JobQueue(get_redis_client())


def get_progress_store() -> JobProgressStore:
    return JobProgressStore(get_redis_client())


def get_storage() -> StorageService:
    return StorageService()


def get_dispatcher(request: Request) -> JobDispatcher:
    pool: ArqRedis = request.app.state.arq_pool
    return JobDispatcher(pool)
