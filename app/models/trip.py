from __future__ import annotations

import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Numeric invitation/share code for joining a trip (6-8 digits; stored as up to 8 chars)
    trip_code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
