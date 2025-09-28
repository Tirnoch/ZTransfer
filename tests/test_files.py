from __future__ import annotations

import hashlib
import re
from pathlib import Path

import sys
from fastapi.testclient import TestClient
from sqlmodel import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.config import get_settings
from app.db import session_scope
from app.models import Upload


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "CSRF token not found"
    return match.group(1)


def _bootstrap_and_login(client: TestClient, email: str, password: str) -> None:
    bootstrap_response = client.post(
        "/auth/invite/bootstrap",
        json={"admin_token": "bootstrap-token", "email": email},
    )
    assert bootstrap_response.status_code == 201
    invite_token = bootstrap_response.json()["invite_token"]

    accept_response = client.post(
        "/auth/invite/accept",
        json={"token": invite_token, "email": email, "password": password},
    )
    assert accept_response.status_code == 201

    login_form = client.get("/auth/login")
    csrf_token = _extract_csrf_token(login_form.text)
    login_response = client.post(
        "/auth/login",
        data={"email": email, "password": password, "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert login_response.status_code == 303


def test_upload_success(test_client: TestClient) -> None:
    _bootstrap_and_login(test_client, "uploader@example.com", "supersecret")

    content = b"hello world"
    response = test_client.post(
        "/files",
        files={"file": ("hello.txt", content, "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["download_url"].endswith("/d/" + payload["download_url"].split("/d/")[-1])
    assert payload["delete_url"].startswith(get_settings().base_url)

    with session_scope() as session:
        upload = session.exec(select(Upload)).one()
        assert upload.size_bytes == len(content)
        assert upload.sha256 == hashlib.sha256(content).hexdigest()
        expected_path = get_settings().resolved_storage_dir / upload.path
        assert expected_path.exists()
        assert expected_path.read_bytes() == content


def test_upload_rejects_large_file(test_client: TestClient) -> None:
    _bootstrap_and_login(test_client, "biguser@example.com", "supersecret")

    settings = get_settings()
    oversize = b"a" * (settings.max_size_bytes + 1)
    response = test_client.post(
        "/files",
        files={"file": ("large.bin", oversize, "application/octet-stream")},
    )

    assert response.status_code == 413
    with session_scope() as session:
        assert session.exec(select(Upload)).first() is None
