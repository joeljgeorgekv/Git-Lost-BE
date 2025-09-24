from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel


class TripUserCreate(BaseModel):
    user_id: uuid.UUID
    trip_id: uuid.UUID
    date_ranges: list[str] | None = None  # e.g., "02-04-2002 - 04-04-2002"
    preferred_places: list[Any] | None = None  # placeholder for List[Place]
    budget: int | None = None
    preferences: list[str] | None = None
    must_haves: list[str] | None = None


class TripUserRead(TripUserCreate):
    pass
