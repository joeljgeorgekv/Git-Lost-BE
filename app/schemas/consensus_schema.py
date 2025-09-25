from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class Dates(BaseModel):
    start: str = Field(..., description="YYYY-MM-DD")
    end: str = Field(..., description="YYYY-MM-DD")
    display: Optional[str] = Field(None, description="Human readable, e.g., 'Nov 14–18, 2025'")
    days: Optional[int] = Field(None, description="Total number of days")
    weekday_span: Optional[str] = Field(None, description="e.g., 'Thursday to Sunday'")


class AreaCard(BaseModel):
    name: str
    summary: Optional[str] = None
    tags: List[str] = []


class BudgetBreakdown(BaseModel):
    flights: Optional[int] = None
    stay: Optional[int] = None
    local: Optional[int] = None


class Budget(BaseModel):
    currency: Literal["INR", "USD", "EUR"] = "INR"
    estimated_per_person: int
    breakdown: Optional[BudgetBreakdown] = None


class ConsensusPayload(BaseModel):
    trip_name: str
    destination: str
    dates: Dates
    areas: List[AreaCard] = []
    budget: Optional[Budget] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ConsensusRequest(BaseModel):
    consensus: ConsensusPayload
