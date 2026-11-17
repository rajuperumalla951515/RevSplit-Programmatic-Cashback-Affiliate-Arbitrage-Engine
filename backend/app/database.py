"""Backward-compatible imports for the shared database module."""

from app.core.database import AsyncSessionLocal, engine, get_db_session

__all__ = ["engine", "AsyncSessionLocal", "get_db_session"]
