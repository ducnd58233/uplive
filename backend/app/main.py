from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import close_database, init_database
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis, init_redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_database()
    await init_redis()
    logger.info("API started")
    yield
    await close_redis()
    await close_database()
    logger.info("API stopped")


app = FastAPI(title="uplive", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
