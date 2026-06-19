import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import ffmpeg

from app.modules.editor.errors import FfmpegError
from app.modules.jobs.domain import TransitionType

OUTPUT_HEIGHT = 720
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
PIX_FMT = "yuv420p"

_XFADE_TRANSITIONS = {
    TransitionType.FADE: "fade",
    TransitionType.SLIDE: "slideleft",
}


def make_test_clip(output_path: Path, duration: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    video = ffmpeg.input(
        f"testsrc=size=320x240:rate=30:duration={duration}",
        f="lavfi",
    )
    audio = ffmpeg.input(f"sine=frequency=440:duration={duration}", f="lavfi")
    _run(
        ffmpeg.output(
            video,
            audio,
            str(output_path),
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            pix_fmt=PIX_FMT,
            shortest=None,
        )
    )


def probe_duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise FfmpegError(completed.stderr.strip() or "ffprobe failed")
    payload = json.loads(completed.stdout)
    duration = payload.get("format", {}).get("duration")
    if duration is None:
        raise FfmpegError("ffprobe did not return duration")
    return float(duration)


def extract(input_path: Path, output_path: Path, start: float, end: float) -> None:
    if start >= end:
        raise ValueError("start must be less than end")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clip_duration = end - start
    _run(
        ffmpeg.input(str(input_path), ss=start, t=clip_duration).output(
            str(output_path),
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            pix_fmt=PIX_FMT,
        )
    )


def concat(inputs: Sequence[Path], output_path: Path) -> None:
    if len(inputs) < 2:
        raise ValueError("concat requires at least two inputs")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_path = output_path.parent / f"{output_path.stem}_concat.txt"
    with list_path.open("w", encoding="utf-8") as handle:
        for clip_path in inputs:
            escaped = str(clip_path.resolve()).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")
    try:
        _run(
            ffmpeg.input(str(list_path), format="concat", safe=0).output(
                str(output_path),
                c="copy",
            )
        )
    finally:
        list_path.unlink(missing_ok=True)


def xfade(
    inputs: Sequence[Path],
    output_path: Path,
    transition: TransitionType,
    transition_duration: float,
) -> None:
    if len(inputs) < 2:
        raise ValueError("xfade requires at least two inputs")
    if transition_duration <= 0:
        raise ValueError("transition_duration must be positive")
    transition_name = _XFADE_TRANSITIONS.get(transition)
    if transition_name is None:
        raise ValueError(f"unsupported transition for xfade: {transition}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    streams = [ffmpeg.input(str(path)) for path in inputs]
    durations = [probe_duration(path) for path in inputs]

    video = streams[0].video
    audio = streams[0].audio
    timeline = durations[0]

    for index in range(1, len(streams)):
        offset = timeline - transition_duration
        video = ffmpeg.filter(
            [video, streams[index].video],
            "xfade",
            transition=transition_name,
            duration=transition_duration,
            offset=offset,
        )
        audio = ffmpeg.filter(
            [audio, streams[index].audio],
            "acrossfade",
            d=transition_duration,
        )
        timeline = timeline + durations[index] - transition_duration

    _run(
        ffmpeg.output(
            video,
            audio,
            str(output_path),
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            pix_fmt=PIX_FMT,
            movflags="+faststart",
        )
    )


def export(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ffmpeg.input(str(input_path)).output(
            str(output_path),
            vf=f"scale=-2:{OUTPUT_HEIGHT}",
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            pix_fmt=PIX_FMT,
            movflags="+faststart",
        )
    )


def _run(stream: ffmpeg.nodes.OutputStream) -> None:
    try:
        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode("utf-8") if exc.stderr else "ffmpeg failed"
        raise FfmpegError(stderr.strip()) from exc
