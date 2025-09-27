"""Background cleanup worker for removing expired uploads."""

from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import select

from . import models
from .db import session_scope
from .storage import STORAGE_ROOT


def delete_expired_uploads(now: datetime | None = None) -> int:
    """Delete expired uploads from disk and database.

    Returns the number of uploads removed.
    """

    timestamp = now or datetime.now(tz=timezone.utc)
    removed = 0
    with session_scope() as session:
        result = session.exec(select(models.Upload).where(models.Upload.expires_at <= timestamp))
        for upload in result:
            _delete_upload_file(Path(upload.path))
            session.delete(upload)
            removed += 1
    return removed


def _delete_upload_file(path: Path) -> None:
    """Remove the file at the given path if it exists."""

    try:
        path.unlink(missing_ok=True)
        # Attempt to clean up now-empty parent directory.
        if path.parent != STORAGE_ROOT:
            path.parent.rmdir()
    except OSError:
        # Directory not empty or other filesystem issue; ignore for now.
        pass
