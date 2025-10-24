"""Common dependency utilities for FastAPI routes."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy.orm import Session

from .config import get_settings
from .core.db.session import SessionLocal


@contextmanager
def get_db() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - transactional rollback
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db() -> AsyncIterator[Session]:
    """Async wrapper around the sync session for background tasks."""

    with get_db() as session:
        yield session


__all__ = ["get_db", "get_async_db", "get_settings"]
