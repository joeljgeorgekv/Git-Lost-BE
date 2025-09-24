from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLAlchemy engine/session. Defaults to local Postgres for dev unless overridden.
# If you're running Postgres via docker-compose, this default matches the compose config
# when connecting from the host (mapped port 5432). If running the app inside Docker,
# set DATABASE_URL to use the service hostname `db` instead of `localhost`.
DATABASE_URL = (
    settings.database_url
    or "postgresql+psycopg://trip:trip@localhost:5432/tripdb"
)

engine = create_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_db():
    """Yield a session for dependency injection in future endpoints.

    Intentionally unused for now.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables for a quickstart hackathon environment.

    In production, use proper migrations (e.g., Alembic) instead of create_all.
    """
    from app.models import Base  # imported here to avoid circular import at module load

    Base.metadata.create_all(bind=engine)
