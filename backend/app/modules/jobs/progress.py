import uuid

from redis.asyncio import Redis

from app.core.config import Settings, get_settings


class JobProgressStore:
    def __init__(
        self,
        redis_client: Redis,
        settings: Settings | None = None,
    ) -> None:
        self._redis = redis_client
        self._settings = settings or get_settings()

    def _key(self, job_id: uuid.UUID) -> str:
        return f"job:{job_id}:progress"

    async def write(self, job_id: uuid.UUID, progress: int) -> None:
        await self._redis.set(
            self._key(job_id),
            str(progress),
            ex=self._settings.state_ttl_seconds,
        )

    async def read(self, job_id: uuid.UUID) -> int | None:
        value = await self._redis.get(self._key(job_id))
        if value is None:
            return None
        return int(value)
