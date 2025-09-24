from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import log_info, log_error
from app.domain.trip_domain import (
    CreateGroupTripRequest,
    AddUserToTripRequest,
)
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])  # Intentionally empty for MVP

service = TripService()


@router.post("", status_code=status.HTTP_200_OK)
def create_group_trip(payload: CreateGroupTripRequest, db: Session = Depends(get_db)):
    log_info("create trip request", trip_name=payload.trip_name, user_id=str(payload.user_id))
    try:
        service.create_group_trip(db, payload)
    except ValueError as e:
        if str(e) == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to create trip")
    return Response(status_code=status.HTTP_200_OK)


@router.post("/add-user", status_code=status.HTTP_200_OK)
def add_user_to_trip(payload: AddUserToTripRequest, db: Session = Depends(get_db)):
    log_info("add user to trip request", trip_id=str(payload.trip_id), user_id=str(payload.user_id))
    try:
        service.add_user_to_trip(db, payload)
    except ValueError as e:
        if str(e) == "trip_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trip not found")
        if str(e) == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to add user to trip")
    return Response(status_code=status.HTTP_200_OK)