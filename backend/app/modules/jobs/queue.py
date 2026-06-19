from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.modules.jobs.errors import QueueFullError


class JobQueue:
    def __init__(
        self,
        redis_client: Redis,
        settings: Settings | None = None,
    ) -> None:
        self._redis = redis_client
        self._settings = settings or get_settings()

    async def depth(self) -> int:
        count = await self._redis.zcard(self._settings.arq_queue_key)
        return int(count)

    async def check_capacity(self) -> None:
        if await self.depth() >= self._settings.queue_size:
            raise QueueFullError()

    async def reserve_slot(self) -> None:
        await self.check_capacity()
        await self._redis.zadd(
            self._settings.arq_queue_key,
            {f"reserved:{await self._redis.time()}": await self.depth()},
        )
