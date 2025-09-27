"""Application entrypoint for the ZTransfer service."""

from __future__ import annotations

import importlib.metadata
import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import select

from .config import settings
from .db import init_db, session_scope
from .storage import ensure_storage_root


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - inherited docstring
        log_payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            log_payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "__dict__", {}).items():
            if key.startswith("ctx_"):
                log_payload[key.removeprefix("ctx_")] = value
        return json.dumps(log_payload, default=str)


def configure_logging() -> None:
    """Attach a JSON formatter to the root logger once."""

    root_logger = logging.getLogger()
    if any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        # Assume logging was configured by the runner (e.g., uvicorn); do nothing.
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


app = FastAPI(title="ZTransfer")


@app.on_event("startup")
def _startup() -> None:
    """Prepare application resources."""

    configure_logging()
    ensure_storage_root()
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Placeholder upload page until the frontend lands."""

    return "<html><body><h1>ZTransfer</h1><p>Upload interface coming soon.</p></body></html>"


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    """Liveness probe endpoint."""

    return {"status": "ok"}


@app.get("/readyz")
def readycheck() -> dict[str, str]:
    """Readiness probe that verifies DB connectivity and storage path."""

    try:
        ensure_storage_root()
        with session_scope() as session:
            session.exec(select(1))
    except Exception as exc:  # pragma: no cover - surfaced via HTTPException
        raise HTTPException(status_code=503, detail="not ready") from exc
    return {"status": "ready"}


@app.get("/version")
def version() -> dict[str, str]:
    """Return application version for monitoring."""

    try:
        package_version = importlib.metadata.version("ztransfer")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - local dev fallback
        package_version = "0.0.0"
    return {"version": package_version}
