"""Database session and engine helpers."""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

_DB_PATH = settings.resolved_db_path

_ENGINE = create_engine(
    f"sqlite:///{_DB_PATH}", echo=False, connect_args={"check_same_thread": False}
)


def init_db() -> None:
    """Create database tables if they do not exist."""

    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(_ENGINE)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    session = Session(_ENGINE, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
