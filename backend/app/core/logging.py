import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import Settings, get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 5

_logging_ready = False


def setup_logging(settings: Settings | None = None) -> None:
    global _logging_ready
    if _logging_ready:
        return

    resolved = settings or get_settings()
    log_dir = Path(resolved.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / resolved.log_file

    level = getattr(logging, resolved.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=resolved.log_max_bytes,
        backupCount=resolved.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "arq"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    _logging_ready = True
    get_logger(__name__).info(
        "log level=%s path=%s",
        resolved.log_level,
        log_path,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def reset_logging() -> None:
    global _logging_ready
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    _logging_ready = False
