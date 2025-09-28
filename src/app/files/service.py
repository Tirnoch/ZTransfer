"""Domain logic for handling file uploads."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Tuple

from fastapi import UploadFile

from ..config import settings
from ..db import session_scope
from ..models import Upload, User
from ..storage import allocate_upload_path, stream_to_disk


class UploadTooLargeError(Exception):
    """Raised when an upload exceeds MAX_SIZE_BYTES."""


class MissingUserIdError(Exception):
    """Raised when the user model lacks a persisted ID."""


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _hash_token(token: str) -> str:
    digest = hashlib.sha256()
    digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def store_upload(user: User, upload_file: UploadFile) -> Tuple[Upload, str, str]:
    """Persist an uploaded file and return its metadata with tokens.

    Returns a tuple of (upload_record, download_token, raw_delete_token).
    """

    if user.id is None:
        raise MissingUserIdError("User must have a persisted ID before uploading")

    now = _now()
    destination_path = allocate_upload_path(user.id, upload_file.filename or "file", now)

    hasher = hashlib.sha256()
    total_bytes = 0

    # Stream the file to disk in chunks while hashing and enforcing limits.
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_path.open("wb") as file_handle:
        while True:
            chunk = upload_file.file.read(settings.chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > settings.max_size_bytes:
                upload_file.file.close()
                destination_path.unlink(missing_ok=True)
                raise UploadTooLargeError("Upload exceeds maximum allowed size")
            file_handle.write(chunk)
            hasher.update(chunk)

    sha256_hex = hasher.hexdigest()
    expires_at = now + timedelta(days=settings.retention_days)

    download_token = token_urlsafe(32)
    delete_token_raw = token_urlsafe(32)
    delete_token_hash = _hash_token(delete_token_raw)

    relative_path = destination_path.relative_to(settings.resolved_storage_dir)

    upload_record = Upload(
        owner_id=user.id,
        download_token=download_token,
        delete_token_hash=delete_token_hash,
        path=str(relative_path),
        original_name=upload_file.filename or "file",
        content_type=upload_file.content_type or "application/octet-stream",
        size_bytes=total_bytes,
        created_at=now,
        expires_at=expires_at,
        sha256=sha256_hex,
    )

    with session_scope() as session:
        session.add(upload_record)
        session.flush()
        session.refresh(upload_record)

    return upload_record, download_token, delete_token_raw
