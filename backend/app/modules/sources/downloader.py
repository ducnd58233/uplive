import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from app.core.config import Settings, get_settings
from app.modules.editor.ffmpeg import probe_duration
from app.modules.sources.errors import DownloadError

MAX_HEIGHT = 720
DEFAULT_TITLE = "Untitled"


@dataclass(frozen=True)
class ProbeResult:
    duration: float
    title: str


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    duration: float
    title: str


class SourceDownloader:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def download(self, url: str, output_path: Path) -> DownloadResult:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        stem = output_path.with_suffix("")
        ydl_opts = {
            "format": (
                f"bestvideo[height<={MAX_HEIGHT}]+bestaudio/best[height<={MAX_HEIGHT}]"
            ),
            "outtmpl": str(stem),
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as exc:
            raise DownloadError(str(exc)) from exc

        if info is None:
            raise DownloadError("yt-dlp returned no metadata")

        downloaded_path = self._resolve_downloaded_path(stem, info)
        if downloaded_path.resolve() != output_path:
            if output_path.exists():
                output_path.unlink()
            downloaded_path.replace(output_path)

        probe = self.probe(output_path)
        title = str(info.get("title") or probe.title)
        return DownloadResult(
            path=output_path,
            duration=probe.duration,
            title=title,
        )

    def probe(self, path: Path) -> ProbeResult:
        duration = probe_duration(path)
        title = self._probe_title(path)
        return ProbeResult(duration=duration, title=title)

    def _resolve_downloaded_path(self, stem: Path, info: dict[str, object]) -> Path:
        requested = info.get("requested_downloads")
        if isinstance(requested, list) and requested:
            first = requested[0]
            if isinstance(first, dict):
                filepath = first.get("filepath")
                if isinstance(filepath, str):
                    return Path(filepath)

        ext = info.get("ext")
        if isinstance(ext, str):
            candidate = stem.with_suffix(f".{ext}")
            if candidate.exists():
                return candidate

        for suffix in (".mp4", ".webm", ".mkv"):
            candidate = stem.with_suffix(suffix)
            if candidate.exists():
                return candidate

        raise DownloadError("downloaded file not found")

    def _probe_title(self, path: Path) -> str:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format_tags=title",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return DEFAULT_TITLE
        payload = json.loads(completed.stdout)
        tags = payload.get("format", {}).get("tags", {})
        if not isinstance(tags, dict):
            return DEFAULT_TITLE
        title = tags.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return DEFAULT_TITLE
