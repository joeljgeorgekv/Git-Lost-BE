from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel


class TripUserCreate(BaseModel):
    user_id: uuid.UUID
    trip_id: uuid.UUID
    preferred_dates: dict | None = None  # placeholder for List[DateRange]
    preferred_places: list[Any] | None = None  # placeholder for List[Place]
    budget: int | None = None
    preferences: list[str] | None = None
    must_haves: list[str] | None = None


class TripUserRead(TripUserCreate):
    pass
