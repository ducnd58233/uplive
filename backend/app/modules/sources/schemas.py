import re

from pydantic import BaseModel, HttpUrl, field_validator

from app.modules.jobs.domain import SourceStatus

YOUTUBE_URL_PATTERN = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
    re.IGNORECASE,
)


class CreateSourceRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def check_youtube_url(cls, value: HttpUrl) -> HttpUrl:
        if not YOUTUBE_URL_PATTERN.match(str(value)):
            raise ValueError("URL must be a valid YouTube watch or youtu.be link")
        return value


class SourceCreatedResponse(BaseModel):
    source_id: str
    status: SourceStatus


class SourceDetailResponse(BaseModel):
    status: SourceStatus
    duration: float | None = None
    title: str | None = None
    error: str | None = None
