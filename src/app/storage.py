"""File storage utilities for streaming uploads and downloads."""

from pathlib import Path
from secrets import token_urlsafe
from typing import BinaryIO

from .config import settings

STORAGE_ROOT = settings.resolved_storage_dir
CHUNK_SIZE = settings.chunk_size


def ensure_storage_root() -> None:
    """Make sure the storage directory exists."""

    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def allocate_upload_path(original_name: str) -> Path:
    """Return a unique storage path for a new upload."""

    ensure_storage_root()
    token = token_urlsafe(16)
    target_dir = STORAGE_ROOT / token
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / original_name


def stream_to_disk(stream: BinaryIO, destination: Path) -> int:
    """Persist the provided binary stream to disk and return the byte count."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with destination.open("wb") as file_handle:
        while chunk := stream.read(CHUNK_SIZE):
            total += len(chunk)
            file_handle.write(chunk)
    return total
