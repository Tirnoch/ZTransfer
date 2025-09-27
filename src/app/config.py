"""Configuration management helpers for ZTransfer."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    storage_dir: Path = Field(default=Path("storage"), description="Base directory for stored files")
    db_path: Path = Field(default=Path("storage/ztransfer.db"), description="SQLite database path")
    max_size_bytes: int = Field(default=5 * 1024 * 1024 * 1024, description="Maximum upload size in bytes")
    retention_days: int = Field(default=10, description="Default retention window in days")
    base_url: str = Field(default="http://localhost:8000", description="Base URL for generated links")
    chunk_size: int = Field(default=4 * 1024 * 1024, description="File stream chunk size in bytes")
    session_secret: str = Field(default="change-me", description="Secret used to sign session cookies")
    admin_bootstrap_token: str | None = Field(default=None, description="Optional token for seeding the first admin user")

    @property
    def resolved_storage_dir(self) -> Path:
        """Return the storage directory with symlinks and user home expanded."""

        return self.storage_dir.expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
