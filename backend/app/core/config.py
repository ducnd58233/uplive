from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://uplive:uplive@localhost:5432/uplive"
    redis_url: str = "redis://localhost:6379/0"
    max_source_seconds: int = 1200
    max_clips: int = 8
    queue_size: int = 10
    work_dir: str = "./work"
    state_ttl_seconds: int = 7200
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_file: str = "uplive.log"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 5
    arq_queue_key: str = "arq:queue"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
