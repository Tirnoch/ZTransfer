"""Database session and engine helpers."""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

_ENGINE = create_engine(
    f"sqlite:///{settings.db_path}", echo=False, connect_args={"check_same_thread": False}
)


def init_db() -> None:
    """Create database tables if they do not exist."""

    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(_ENGINE)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    session = Session(_ENGINE)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
