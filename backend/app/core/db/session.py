"""Database session factory configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ...config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

__all__ = ["engine", "SessionLocal"]
