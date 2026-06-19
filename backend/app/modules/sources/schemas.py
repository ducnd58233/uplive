import re

from pydantic import BaseModel, HttpUrl, field_validator

YOUTUBE_URL_PATTERN = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
    re.IGNORECASE,
)


class CreateSourceRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, value: HttpUrl) -> HttpUrl:
        if not YOUTUBE_URL_PATTERN.match(str(value)):
            raise ValueError("URL must be a valid YouTube watch or youtu.be link")
        return value
