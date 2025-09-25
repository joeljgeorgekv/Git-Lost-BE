from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel


class CreateGroupTripRequest(BaseModel):
    trip_name: str
    user_id: uuid.UUID
    # Optional planning inputs (all optional for MVP)
    date_ranges: list[str] | None = None
    preferred_places: list[Any] | None = None
    budget: int | None = None
    preferences: list[str] | None = None
    must_haves: list[str] | None = None

class CreateTripResponse(BaseModel):
    trip_id: uuid.UUID


class TripSummary(BaseModel):
    id: str  # UUID as string for client compatibility
    trip_name: str
    latest_message: str | None = None
    latest_message_at: str | None = None  # ISO timestamp string


class ListTripsResponse(BaseModel):
    trips: list[TripSummary]


class AddUserToTripRequest(BaseModel):
    trip_id: uuid.UUID
    user_id: uuid.UUID
    date_ranges: list[str] | None = None
    preferred_places: list[Any] | None = None
    budget: int | None = None
    preferences: list[str] | None = None
    must_haves: list[str] | None = None
