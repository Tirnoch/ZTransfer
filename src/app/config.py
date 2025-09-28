"""Configuration management helpers for ZTransfer."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_path(path_value: Path) -> Path:
    """Expand user/home references and resolve relative paths."""

    expanded = path_value.expanduser()
    if expanded.is_absolute():
        return expanded.resolve()
    return (Path.cwd() / expanded).resolve()


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
    session_cookie_name: str = Field(default="ztransfer_session", description="Name of the session cookie")
    csrf_cookie_name: str = Field(default="ztransfer_csrf", description="Name of the CSRF cookie for forms")
    cookie_secure: bool = Field(default=False, description="Whether auth cookies require HTTPS")
    cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax", description="SameSite attribute for cookies")
    session_ttl_hours: int = Field(default=24 * 7, description="Session lifetime in hours")
    csrf_token_ttl_minutes: int = Field(default=30, description="Time-to-live for CSRF token in minutes")
    invite_ttl_hours: int = Field(default=48, description="Invite token lifetime in hours")

    @property
    def resolved_storage_dir(self) -> Path:
        """Return the storage directory with symlinks and user home expanded."""

        return _resolve_path(self.storage_dir)

    @property
    def resolved_db_path(self) -> Path:
        """Return the absolute path to the SQLite database file."""

        return _resolve_path(self.db_path)

    @property
    def session_cookie_max_age(self) -> int:
        """Session lifetime in seconds."""

        return self.session_ttl_hours * 3600

    @property
    def csrf_token_max_age(self) -> int:
        """CSRF token lifetime in seconds."""

        return self.csrf_token_ttl_minutes * 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
