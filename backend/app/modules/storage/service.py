import shutil
import time
from pathlib import Path

from app.core.config import Settings, get_settings


class StorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._root = Path(self._settings.work_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def job_dir(self, job_id: str) -> Path:
        path = self._root / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def source_path(self, source_id: str, filename: str = "source.mp4") -> Path:
        return self.job_dir(source_id) / filename

    def result_path(self, job_id: str, filename: str = "result.mp4") -> Path:
        return self.job_dir(job_id) / filename

    def cleanup(self, workspace_id: str) -> None:
        path = self._root / workspace_id
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def is_expired(self, created_at_timestamp: float) -> bool:
        age_seconds = time.time() - created_at_timestamp
        return age_seconds > self._settings.state_ttl_seconds
