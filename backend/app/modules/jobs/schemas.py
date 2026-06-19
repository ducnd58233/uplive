from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.jobs.domain import TransitionType


class ClipRange(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_range(self) -> "ClipRange":
        if self.start >= self.end:
            raise ValueError("start must be less than end")
        return self


class CreateJobRequest(BaseModel):
    source_id: str
    clips: list[ClipRange]
    transition: TransitionType
    transition_duration: float = Field(default=0.0, ge=0)

    @field_validator("clips")
    @classmethod
    def validate_clip_count(cls, value: list[ClipRange]) -> list[ClipRange]:
        if not value:
            raise ValueError("clips must not be empty")
        return value

    @model_validator(mode="after")
    def validate_transition_duration(self) -> "CreateJobRequest":
        if self.transition != TransitionType.CUT and self.transition_duration <= 0:
            raise ValueError("transition_duration must be positive for fade and slide")
        return self


def validate_clips_against_duration(
    clips: list[ClipRange],
    duration: float,
    max_clips: int,
    max_source_seconds: float,
) -> None:
    if duration > max_source_seconds:
        raise ValueError(f"source duration exceeds {max_source_seconds} seconds")
    if len(clips) > max_clips:
        raise ValueError(f"clips count exceeds {max_clips}")
    for clip in clips:
        if clip.end > duration:
            raise ValueError("clip end exceeds source duration")
