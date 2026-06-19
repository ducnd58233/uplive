import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SourceStatus(StrEnum):
    DOWNLOADING = "downloading"
    READY = "ready"
    ERROR = "error"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class TransitionType(StrEnum):
    CUT = "cut"
    FADE = "fade"
    SLIDE = "slide"


@dataclass(frozen=True)
class SourceRecord:
    id: uuid.UUID
    url: str
    status: SourceStatus
    duration: float | None
    title: str | None
    path: str | None
    error: str | None
    created_at: datetime


@dataclass(frozen=True)
class JobRecord:
    id: uuid.UUID
    source_id: uuid.UUID
    clips: list[dict[str, float]]
    transition: TransitionType
    transition_duration: float
    status: JobStatus
    progress: int
    result_path: str | None
    error: str | None
    created_at: datetime
