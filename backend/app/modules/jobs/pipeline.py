import asyncio
import uuid
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.modules.editor.errors import EditorError
from app.modules.editor.service import EditorService
from app.modules.jobs.domain import SourceStatus
from app.modules.jobs.errors import JobNotFoundError, SourceNotFoundError
from app.modules.jobs.progress import JobProgressStore
from app.modules.jobs.store import JobStore
from app.modules.sources.errors import SourceError
from app.modules.sources.service import SourceService
from app.modules.storage.service import StorageService

logger = get_logger(__name__)

EXTRACT_PROGRESS_MAX = 60
MERGE_PROGRESS = 80
EXPORT_PROGRESS = 90
DONE_PROGRESS = 100


class JobPipeline:
    def __init__(
        self,
        job_store: JobStore,
        progress_store: JobProgressStore,
        source_service: SourceService | None = None,
        editor_service: EditorService | None = None,
        storage: StorageService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._job_store = job_store
        self._progress_store = progress_store
        self._source_service = source_service or SourceService()
        self._editor_service = editor_service or EditorService()
        self._storage = storage or StorageService()
        self._settings = settings or get_settings()

    async def run_source_download(self, source_id: uuid.UUID, url: str) -> None:
        source_key = str(source_id)
        try:
            fetched = await asyncio.to_thread(
                self._source_service.download_source,
                source_key,
                url,
            )
            await self._job_store.mark_source_ready(
                source_id,
                duration=fetched.duration,
                title=fetched.title,
                path=fetched.path,
            )
        except SourceError as exc:
            await self._fail_source_download(source_id, str(exc))
            raise
        except Exception as exc:
            await self._fail_source_download(source_id, str(exc))
            raise

    async def run_job_render(self, job_id: uuid.UUID) -> None:
        job_key = str(job_id)
        clip_paths: list[Path] = []
        merged_path: Path | None = None
        try:
            job = await self._job_store.get_job(job_id)
            if job is None:
                raise JobNotFoundError(str(job_id))

            source = await self._job_store.get_source(job.source_id)
            if source is None or source.path is None:
                raise SourceNotFoundError(str(job.source_id))
            if source.status != SourceStatus.READY:
                raise SourceError(f"source {job.source_id} is not ready")

            await self._job_store.mark_job_processing(job_id)
            await self._set_progress(job_id, 0)

            source_path = Path(source.path)
            job_dir = self._storage.job_dir(job_key)
            clip_count = len(job.clips)

            for index, clip in enumerate(job.clips):
                clip_path = job_dir / f"clip_{index}.mp4"
                await asyncio.to_thread(
                    self._editor_service.extract,
                    source_path,
                    clip_path,
                    clip["start"],
                    clip["end"],
                )
                clip_paths.append(clip_path)
                extract_progress = int((index + 1) / clip_count * EXTRACT_PROGRESS_MAX)
                await self._set_progress(job_id, extract_progress)

            merged_path = job_dir / "merged.mp4"
            await asyncio.to_thread(
                self._editor_service.merge_clips,
                clip_paths,
                merged_path,
                job.transition,
                job.transition_duration,
            )
            await self._set_progress(job_id, MERGE_PROGRESS)

            result_path = self._storage.result_path(job_key)
            await asyncio.to_thread(
                self._editor_service.export,
                merged_path,
                result_path,
            )
            await self._set_progress(job_id, EXPORT_PROGRESS)

            await self._job_store.mark_job_done(job_id, str(result_path))
            await self._set_progress(job_id, DONE_PROGRESS)
            self._remove_temp_files(clip_paths, merged_path)
        except (JobNotFoundError, SourceNotFoundError, SourceError, EditorError) as exc:
            await self._fail_job_render(job_id, str(exc))
            raise
        except Exception as exc:
            await self._fail_job_render(job_id, str(exc))
            raise

    async def _set_progress(self, job_id: uuid.UUID, progress: int) -> None:
        await self._progress_store.write(job_id, progress)
        await self._job_store.update_job_progress(job_id, progress)

    async def _fail_source_download(
        self,
        source_id: uuid.UUID,
        error: str,
    ) -> None:
        logger.error("source download failed source_id=%s error=%s", source_id, error)
        await self._job_store.mark_source_error(source_id, error)
        self._storage.cleanup(str(source_id))

    async def _fail_job_render(self, job_id: uuid.UUID, error: str) -> None:
        logger.error("job render failed job_id=%s error=%s", job_id, error)
        await self._job_store.mark_job_error(job_id, error)
        self._storage.cleanup(str(job_id))

    def _remove_temp_files(
        self,
        clip_paths: list[Path],
        merged_path: Path | None,
    ) -> None:
        for clip_path in clip_paths:
            clip_path.unlink(missing_ok=True)
        if merged_path is not None:
            merged_path.unlink(missing_ok=True)
