"""
app/core/database.py
─────────────────────
PostgreSQL (SQLAlchemy sync) + MongoDB (Motor async) setup.

Usage:
    from app.core.database import get_db, get_mongo_db

FastAPI dependency injection:
    async def route(db: Session = Depends(get_db)):
        ...
"""
from __future__ import annotations

from typing import AsyncGenerator, Generator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL (SQLAlchemy)
# ─────────────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,          # detect stale connections
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,         # SQL logging in dev
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared base for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables (called at startup)."""
    Base.metadata.create_all(bind=engine)


# ─────────────────────────────────────────────────────────────────────────────
# MongoDB (Motor — async)
# ─────────────────────────────────────────────────────────────────────────────
_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    return _mongo_client


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency: yields Motor database."""
    client = get_mongo_client()
    try:
        yield client[settings.mongo_db]
    finally:
        pass  # Motor manages connection pool internally


async def close_mongo() -> None:
    """Call on app shutdown."""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None