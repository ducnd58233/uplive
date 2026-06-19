import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings
from app.core.deps import (
    get_dispatcher,
    get_job_queue,
    get_job_store,
    get_progress_store,
    get_storage,
)
from app.modules.jobs.dispatcher import JobDispatcher
from app.modules.jobs.domain import JobStatus, SourceStatus
from app.modules.jobs.errors import QueueFullError, SourceNotFoundError
from app.modules.jobs.progress import JobProgressStore
from app.modules.jobs.queue import JobQueue
from app.modules.jobs.schemas import (
    CreateJobRequest,
    JobCreatedResponse,
    JobDetailResponse,
    check_clips_fit,
)
from app.modules.jobs.store import JobStore
from app.modules.storage.service import StorageService

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", status_code=201, response_model=JobCreatedResponse)
async def create_job(
    body: CreateJobRequest,
    job_store: JobStore = Depends(get_job_store),
    job_queue: JobQueue = Depends(get_job_queue),
    dispatcher: JobDispatcher = Depends(get_dispatcher),
    settings: Settings = Depends(get_settings),
) -> JobCreatedResponse:
    try:
        await job_queue.check_capacity()
    except QueueFullError as exc:
        raise HTTPException(status_code=503, detail="queue full") from exc

    try:
        source_id = uuid.UUID(body.source_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid source_id") from exc

    source = await job_store.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    if source.status != SourceStatus.READY or source.duration is None:
        raise HTTPException(status_code=422, detail="source not ready")

    try:
        check_clips_fit(
            body.clips,
            duration=source.duration,
            max_clips=settings.max_clips,
            max_source_seconds=settings.max_source_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    clips_payload = [{"start": clip.start, "end": clip.end} for clip in body.clips]
    try:
        job = await job_store.create_job(
            source_id,
            clips_payload,
            body.transition,
            body.transition_duration,
        )
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="source not found") from exc

    await dispatcher.dispatch_render(job.id)
    return JobCreatedResponse(job_id=str(job.id), status=job.status)


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: uuid.UUID,
    job_store: JobStore = Depends(get_job_store),
    progress_store: JobProgressStore = Depends(get_progress_store),
) -> JobDetailResponse:
    job = await job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    progress = job.progress
    live_progress = await progress_store.read(job_id)
    if live_progress is not None:
        progress = live_progress
    return JobDetailResponse(
        status=job.status,
        progress=progress,
        error=job.error,
    )


@router.get("/{job_id}/download")
async def download_job(
    job_id: uuid.UUID,
    job_store: JobStore = Depends(get_job_store),
    storage: StorageService = Depends(get_storage),
) -> FileResponse:
    job = await job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status != JobStatus.DONE or not job.result_path:
        raise HTTPException(status_code=404, detail="result not ready")
    path = Path(job.result_path)
    if not path.is_file():
        fallback = storage.result_path(str(job_id))
        if not fallback.is_file():
            raise HTTPException(status_code=404, detail="result file missing")
        path = fallback
    return FileResponse(
        path,
        media_type="video/mp4",
        filename="result.mp4",
        content_disposition_type="attachment",
    )
