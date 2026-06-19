import logging
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.logging import get_logger, reset_logging, setup_logging


@pytest.fixture(autouse=True)
def isolated_logging() -> None:
    reset_logging()
    yield
    reset_logging()


def test_setup_logging_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    settings = Settings(log_dir=str(log_dir), log_file="app.log")

    setup_logging(settings)

    assert log_dir.is_dir()


def test_setup_logging_writes_file(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    settings = Settings(log_dir=str(log_dir), log_file="app.log")
    setup_logging(settings)

    logger = get_logger("test.file")
    message = "file-log-check"
    logger.info(message)

    for handler in logging.getLogger().handlers:
        handler.flush()

    log_content = (log_dir / "app.log").read_text(encoding="utf-8")
    assert message in log_content


def test_setup_logging_once(tmp_path: Path) -> None:
    settings = Settings(log_dir=str(tmp_path / "logs"), log_file="app.log")
    setup_logging(settings)
    handler_count = len(logging.getLogger().handlers)

    setup_logging(settings)

    assert len(logging.getLogger().handlers) == handler_count


def test_get_logger_name() -> None:
    logger = get_logger("app.modules.jobs")

    assert logger.name == "app.modules.jobs"
