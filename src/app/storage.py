"""File storage utilities for streaming uploads and downloads."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from secrets import token_urlsafe
from typing import BinaryIO
from uuid import uuid4

from .config import settings

STORAGE_ROOT = settings.resolved_storage_dir
CHUNK_SIZE = settings.chunk_size
_SAFE_CHARS_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def ensure_storage_root() -> None:
    """Make sure the storage directory exists."""

    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def sanitize_filename(original_name: str) -> str:
    """Return a filesystem-friendly filename, preserving extension."""

    if not original_name:
        return "file"
    sanitized = original_name.strip().replace(" ", "_")
    sanitized = _SAFE_CHARS_PATTERN.sub("", sanitized)
    return sanitized or "file"


def allocate_upload_path(owner_id: int, original_name: str, created_at: datetime) -> Path:
    """Return a deterministic storage path for a new upload."""

    ensure_storage_root()
    safe_name = sanitize_filename(original_name)
    owner_segment = str(owner_id)
    date_segment = created_at.strftime("%Y-%m")
    unique_segment = uuid4().hex
    target_dir = STORAGE_ROOT / owner_segment / date_segment / unique_segment
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / safe_name


def stream_to_disk(stream: BinaryIO, destination: Path) -> int:
    """Persist the provided binary stream to disk and return the byte count."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with destination.open("wb") as file_handle:
        while chunk := stream.read(CHUNK_SIZE):
            total += len(chunk)
            file_handle.write(chunk)
    return total
