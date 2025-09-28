from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

MODULES_TO_RELOAD: Iterable[str] = [
    "app.config",
    "app.deps.security",
    "app.storage",
    "app.db",
    "app.auth",
    "app.main",
]


def _reload_modules() -> None:
    for module_name in MODULES_TO_RELOAD:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)


@pytest.fixture
def test_client(tmp_path, monkeypatch) -> TestClient:
    src_path = Path(__file__).resolve().parents[1] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    storage_dir = tmp_path / "storage"
    db_path = storage_dir / "ztransfer.db"

    monkeypatch.setenv("STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_TOKEN", "bootstrap-token")
    monkeypatch.setenv("SESSION_COOKIE_NAME", "test_session")
    monkeypatch.setenv("CSRF_COOKIE_NAME", "test_csrf")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("COOKIE_SAMESITE", "lax")
    monkeypatch.setenv("SESSION_TTL_HOURS", "24")
    monkeypatch.setenv("CSRF_TOKEN_TTL_MINUTES", "60")
    monkeypatch.setenv("INVITE_TTL_HOURS", "24")

    from app import config as app_config

    app_config.get_settings.cache_clear()
    _reload_modules()

    from app.main import app

    with TestClient(app) as client:
        yield client

    app_config.get_settings.cache_clear()
