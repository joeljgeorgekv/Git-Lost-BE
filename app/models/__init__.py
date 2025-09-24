from __future__ import annotations

# SQLAlchemy Base placeholder (no migrations in MVP)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import only stable models (chat models removed to avoid FK mismatch)
from . import trip  # noqa: F401
from . import trip_user  # noqa: F401
from . import user  # noqa: F401
