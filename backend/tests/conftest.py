import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db.base import Base
from app.modules.jobs.models.job_row import JobRow
from app.modules.jobs.models.source_row import SourceRow


def _prepend_ffmpeg_path() -> None:
    """Test-only helper for local pytest when ffmpeg is not on PATH (e.g. Windows conda)."""
    if shutil.which("ffmpeg"):
        return
    candidates: list[Path] = []
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        candidates.append(Path(conda_prefix) / "Library" / "bin")
    home = Path.home()
    candidates.extend(
        [
            home / "miniconda3" / "envs" / "uplive" / "Library" / "bin",
            home / "anaconda3" / "envs" / "uplive" / "Library" / "bin",
        ]
    )
    for candidate in candidates:
        if (candidate / "ffmpeg.exe").exists() or (candidate / "ffmpeg").exists():
            path_prefix = str(candidate) + os.pathsep
            os.environ["PATH"] = path_prefix + os.environ.get("PATH", "")
            return


_prepend_ffmpeg_path()


def _create_test_tables(connection) -> None:
    Base.metadata.create_all(
        bind=connection,
        tables=[SourceRow.__table__, JobRow.__table__],
    )


@pytest.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(_create_test_tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
def fake_redis():
    import fakeredis.aioredis

    return fakeredis.aioredis.FakeRedis(decode_responses=True)
