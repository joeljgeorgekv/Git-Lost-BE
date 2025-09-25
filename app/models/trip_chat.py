from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.models import Base


class TripChatMessage(Base):
    """Simple chat log tied to a trip.

    Fields:
    - trip_id: FK to trips.id
    - username: who sent the message (free text for MVP)
    - message: message body
    - created_at: message timestamp (server time)
    - chat_status: status of the chat message ('new' or 'Summarized')
    """

    __tablename__ = "trip_chat_messages"

    class ChatStatus(PyEnum):
        NEW = "new"
        SUMMARIZED = "Summarized"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(PG_UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    chat_status = Column(SAEnum(ChatStatus, name="chat_status_enum"), nullable=False, default=ChatStatus.NEW, index=True)
    consensus = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_trip_chat_trip_time", "trip_id", "created_at"),
    )
