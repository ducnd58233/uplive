import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.deps import get_dispatcher, get_job_store
from app.modules.jobs.dispatcher import JobDispatcher
from app.modules.jobs.domain import SourceStatus
from app.modules.jobs.store import JobStore
from app.modules.sources.schemas import (
    CreateSourceRequest,
    SourceCreatedResponse,
    SourceDetailResponse,
)

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("", status_code=201, response_model=SourceCreatedResponse)
async def create_source(
    body: CreateSourceRequest,
    job_store: JobStore = Depends(get_job_store),
    dispatcher: JobDispatcher = Depends(get_dispatcher),
) -> SourceCreatedResponse:
    source = await job_store.create_source(str(body.url))
    await dispatcher.dispatch_source_download(source.id, source.url)
    return SourceCreatedResponse(source_id=str(source.id), status=source.status)


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(
    source_id: uuid.UUID,
    job_store: JobStore = Depends(get_job_store),
) -> SourceDetailResponse:
    source = await job_store.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    return SourceDetailResponse(
        status=source.status,
        duration=source.duration,
        title=source.title,
        error=source.error,
    )


@router.get("/{source_id}/preview")
async def preview_source(
    source_id: uuid.UUID,
    job_store: JobStore = Depends(get_job_store),
) -> FileResponse:
    source = await job_store.get_source(source_id)
    if source is None or source.status != SourceStatus.READY or source.path is None:
        raise HTTPException(status_code=404, detail="preview not available")
    path = Path(source.path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="preview file missing")
    return FileResponse(path, media_type="video/mp4")
