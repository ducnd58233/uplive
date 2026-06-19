import uuid

from arq import ArqRedis


class JobDispatcher:
    def __init__(self, arq_pool: ArqRedis) -> None:
        self._pool = arq_pool

    async def dispatch_source_download(self, source_id: uuid.UUID, url: str) -> None:
        await self._pool.enqueue_job(
            "download_source",
            str(source_id),
            url,
        )

    async def dispatch_render(self, job_id: uuid.UUID) -> None:
        await self._pool.enqueue_job("render_job", str(job_id))
