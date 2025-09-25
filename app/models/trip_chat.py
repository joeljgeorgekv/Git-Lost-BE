from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models import Base


class TripChatMessage(Base):
    """Simple chat log tied to a trip.

    Fields:
    - trip_id: FK to trips.id
    - username: who sent the message (free text for MVP)
    - message: message body
    - created_at: message timestamp (server time)
    """

    __tablename__ = "trip_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(PG_UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_trip_chat_trip_time", "trip_id", "created_at"),
    )
