"""SQLAlchemy base configuration."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lex_pdftotext.db")

# SQLAlchemy base
Base = declarative_base()


@lru_cache
def get_engine():
    """Get SQLAlchemy engine (cached)."""
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def get_session_factory():
    """Get session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_session() -> Generator[Session, None, None]:
    """Get database session (dependency injection)."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=get_engine())
