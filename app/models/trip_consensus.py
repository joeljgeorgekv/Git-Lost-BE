from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON

from app.models import Base


class TripConsensus(Base):
    """Persistent state for trip consensus processing.
    
    This table stores the ongoing consensus state for each trip, allowing
    incremental processing as new messages arrive.
    """

    __tablename__ = "trip_consensus"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: __import__('uuid').uuid4())
    trip_id = Column(PG_UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Current processing state
    status = Column(String(50), nullable=False, default="processing", index=True)  # processing, multiple_candidates, finalized, no_new_messages, error
    iteration_count = Column(Integer, nullable=False, default=0)  # Track iterations to force convergence after 3 rounds
    
    # Structured data (JSON fields)
    summary = Column(JSON, nullable=True)  # Extracted summary from messages
    candidates = Column(JSON, nullable=True)  # List of candidate places
    consensus_card = Column(JSON, nullable=True)  # Final consensus card if finalized
    
    # Metadata
    last_processed_message_id = Column(Integer, nullable=True)  # Track which messages we've processed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index("ix_trip_consensus_trip_status", "trip_id", "status"),
        Index("ix_trip_consensus_updated", "updated_at"),
    )
