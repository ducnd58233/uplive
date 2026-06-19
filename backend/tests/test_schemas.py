import pytest
from pydantic import ValidationError

from app.modules.jobs.schemas import (
    ClipRange,
    CreateJobRequest,
    validate_clips_against_duration,
)
from app.modules.sources.schemas import CreateSourceRequest


def test_create_source_rejects_non_youtube_url() -> None:
    with pytest.raises(ValidationError):
        CreateSourceRequest(url="https://example.com/video")


def test_create_source_accepts_youtube_url() -> None:
    request = CreateSourceRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "youtube.com" in str(request.url)


def test_clip_range_requires_start_before_end() -> None:
    with pytest.raises(ValidationError):
        ClipRange(start=10.0, end=5.0)


def test_create_job_requires_transition_duration_for_fade() -> None:
    with pytest.raises(ValidationError):
        CreateJobRequest(
            source_id="00000000-0000-0000-0000-000000000001",
            clips=[ClipRange(start=0.0, end=1.0)],
            transition="fade",
            transition_duration=0.0,
        )


def test_validate_clips_against_duration_bounds() -> None:
    clips = [ClipRange(start=0.0, end=5.0)]
    validate_clips_against_duration(
        clips,
        duration=10.0,
        max_clips=8,
        max_source_seconds=1200,
    )

    with pytest.raises(ValueError, match="exceeds source duration"):
        validate_clips_against_duration(
            clips,
            duration=3.0,
            max_clips=8,
            max_source_seconds=1200,
        )
