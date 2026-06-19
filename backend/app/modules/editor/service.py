from collections.abc import Sequence
from pathlib import Path

from app.modules.editor import ffmpeg as ffmpeg_helpers
from app.modules.jobs.domain import TransitionType


class EditorService:
    def extract(
        self,
        input_path: Path,
        output_path: Path,
        start: float,
        end: float,
    ) -> None:
        ffmpeg_helpers.extract(input_path, output_path, start, end)

    def merge_clips(
        self,
        clip_paths: Sequence[Path],
        output_path: Path,
        transition: TransitionType,
        transition_duration: float,
    ) -> None:
        if transition == TransitionType.CUT:
            ffmpeg_helpers.concat(clip_paths, output_path)
            return
        ffmpeg_helpers.xfade(
            clip_paths,
            output_path,
            transition,
            transition_duration,
        )

    def export(self, input_path: Path, output_path: Path) -> None:
        ffmpeg_helpers.export(input_path, output_path)
