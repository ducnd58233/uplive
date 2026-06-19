from redis.asyncio import Redis

from app.core.config import Settings, get_settings

_redis: Redis | None = None


def create_redis_client(settings: Settings | None = None) -> Redis:
    resolved = settings or get_settings()
    return Redis.from_url(resolved.redis_url, decode_responses=True)


def get_redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = create_redis_client()
    return _redis


async def init_redis(settings: Settings | None = None) -> Redis:
    global _redis
    _redis = create_redis_client(settings)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
    _redis = None
