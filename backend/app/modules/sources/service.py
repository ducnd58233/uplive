from dataclasses import dataclass

from app.modules.sources.downloader import SourceDownloader
from app.modules.storage.service import StorageService


@dataclass(frozen=True)
class FetchedSource:
    path: str
    duration: float
    title: str


class SourceService:
    def __init__(
        self,
        storage: StorageService | None = None,
        downloader: SourceDownloader | None = None,
    ) -> None:
        self._storage = storage or StorageService()
        self._downloader = downloader or SourceDownloader()

    def download_source(self, source_id: str, url: str) -> FetchedSource:
        output_path = self._storage.source_path(source_id)
        result = self._downloader.download(url, output_path)
        return FetchedSource(
            path=str(result.path),
            duration=result.duration,
            title=result.title,
        )

    def probe_existing(self, source_id: str) -> FetchedSource:
        path = self._storage.source_path(source_id)
        probe = self._downloader.probe(path)
        return FetchedSource(
            path=str(path),
            duration=probe.duration,
            title=probe.title,
        )
