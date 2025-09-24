from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.trip import Trip
from app.models.trip_user import TripUser
from app.models.user import User
from app.core.logger import log_info, log_error

router = APIRouter(prefix="/trips", tags=["trips"])  # Intentionally empty for MVP


class CreateGroupTripRequest(BaseModel):
    trip_name: str
    user_id: uuid.UUID
    # Optional planning inputs (all optional for MVP)
    date_ranges: list[str] | None = None
    preferred_places: list[Any] | None = None
    budget: int | None = None
    preferences: list[str] | None = None
    must_haves: list[str] | None = None


@router.post("", status_code=status.HTTP_200_OK)
def create_group_trip(payload: CreateGroupTripRequest, db: Session = Depends(get_db)):
    log_info("create trip request", trip_name=payload.trip_name, user_id=str(payload.user_id))
    # Validate user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        log_error("create trip failed - user not found", user_id=str(payload.user_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    # Create Trip
    trip = Trip(trip_name=payload.trip_name)
    db.add(trip)
    db.flush()  # to get trip.id without committing yet

    # Link user to trip with their preferences
    tu = TripUser(
        user_id=payload.user_id,
        trip_id=trip.id,
        date_ranges=payload.date_ranges,
        preferred_places=payload.preferred_places,
        budget=payload.budget,
        preferences=payload.preferences,
        must_haves=payload.must_haves,
    )
    db.add(tu)
    db.commit()

    log_info("trip created", trip_id=str(trip.id), user_id=str(payload.user_id))
    # Return 200 with no response body
    return Response(status_code=status.HTTP_200_OK)

