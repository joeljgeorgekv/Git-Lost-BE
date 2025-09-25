from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class GroupPlanRequest(BaseModel):
    """Batch planning request from multiple user messages with optional prior summary."""
    messages: List[Dict[str, Any]]  # items: role, content, optional user/name
    previous_summary: Optional[str] = None
    days: Optional[int] = 3
    model: Optional[str] = "gpt-3.5-turbo"


class GroupPlanResponse(BaseModel):
    """Structured planning response with extracted info and itinerary."""
    summary: str
    extracted_preferences: Dict[str, Any]
    suggestions: List[str]
    itinerary: Dict[str, Any]
    model: Optional[str] = None
    tokens_used: Optional[int] = None
