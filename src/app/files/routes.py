"""Routes handling file upload operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..auth.dependencies import require_auth
from ..config import settings
from ..models import UploadResponse, User
from .service import MissingUserIdError, UploadTooLargeError, store_upload

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
) -> UploadResponse:
    """Stream an uploaded file to disk, returning download/delete URLs."""

    try:
        upload_record, download_token, delete_token = store_upload(current_user, file)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except MissingUserIdError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        file.file.close()

    download_url = f"{settings.base_url}/d/{download_token}"
    delete_url = f"{settings.base_url}/files/{download_token}?delete_token={delete_token}"

    return UploadResponse(download_url=download_url, delete_url=delete_url)
