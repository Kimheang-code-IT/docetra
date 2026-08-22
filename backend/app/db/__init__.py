from app.db.base import Base, utcnow
from app.db.session import SessionLocal, engine, get_db

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "utcnow",
]


def __getattr__(name: str):
    """Lazy re-export ORM models for backward-compatible `from app.db import User` imports."""
    from app import models as _models

    if hasattr(_models, name):
        return getattr(_models, name)
    raise AttributeError(f"module 'app.db' has no attribute {name!r}")
