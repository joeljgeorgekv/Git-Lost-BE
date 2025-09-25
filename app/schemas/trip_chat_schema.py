from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field
 

class TripChatCreate(BaseModel):
    """Request body to create a trip chat message."""
    trip_id: UUID = Field(..., description="ID of the trip this message belongs to")
    username: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)
    time: Optional[datetime] = Field(default=None, description="Optional message timestamp; defaults to server time")


class TripChatResponse(BaseModel):
    """Response for a created/returned trip chat message."""
    id: int
    trip_id: UUID
    username: str
    message: str
    time: datetime
    consensus: Dict[str, Any] | None = None
