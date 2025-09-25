from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.consensus_schema import ConsensusPayload


class ConsensusChatRequest(BaseModel):
    """Request to drive chat after consensus, with a single latest user message.
    The server can optionally keep the short history for better context.
    """

    # Latest user message and optional recent history
    user_message: str
    messages: List[Dict[str, Any]] = []

    # The consensus payload from the UI
    consensus: ConsensusPayload

    # Optional hints
    origin_city: Optional[str] = None
    needs_flight: Optional[bool] = None  # if None, the service will infer
    passengers: int = 2
    budget_range: Optional[str] = "mid-range"

    # Pagination knobs
    flights_limit: int = 3
    flights_offset: int = 0
    hotels_limit: int = 5
    hotels_offset: int = 0
    cabs_limit: int = 5
    cabs_transfer_offset: int = 0
    cabs_day_offset: int = 0


class ConsensusChatResponse(BaseModel):
    """Flexible response returning next-step options and guidance."""

    data: Dict[str, Any] = Field(default_factory=dict)
