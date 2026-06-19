from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_database, init_database
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis, init_redis
from app.modules.jobs.router import router as jobs_router
from app.modules.sources.router import router as sources_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    await init_database(settings)
    await init_redis(settings)
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    app.state.arq_pool = await create_pool(redis_settings)
    logger.info("API started")
    yield
    await app.state.arq_pool.close()
    await close_redis()
    await close_database()
    logger.info("API stopped")


app = FastAPI(title="uplive", version="0.1.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources_router)
app.include_router(jobs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
