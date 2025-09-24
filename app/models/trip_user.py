from __future__ import annotations

import uuid
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON

from app.models import Base


class TripUser(Base):
    __tablename__ = "trip_users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trips.id"), primary_key=True
    )
    date_ranges: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    preferred_places: Mapped[list | None] = mapped_column(JSON, nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferences: Mapped[list | None] = mapped_column(JSON, nullable=True)
    must_haves: Mapped[list | None] = mapped_column(JSON, nullable=True)
