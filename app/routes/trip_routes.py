from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import log_info, log_error
from app.domain.trip_domain import CreateGroupTripRequest, AddUserToTripRequest, CreateTripResponse, ListTripsResponse
from app.services.trip_service import TripService
from app.models.user import User
from app.models.trip import Trip
router = APIRouter(prefix="/trips", tags=["trips"])  # Intentionally empty for MVP

service = TripService()


@router.post("", status_code=status.HTTP_200_OK, response_model=CreateTripResponse)
def create_group_trip(payload: CreateGroupTripRequest, db: Session = Depends(get_db)) -> CreateTripResponse:
    log_info("create trip request", trip_name=payload.trip_name, user_id=str(payload.user_id))
    try:
        return service.create_group_trip(db, payload)
    except ValueError as e:
        if str(e) == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to create trip")


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
    return Response(status_code=status.HTTP_200_OK)


@router.get("/by-user/{username}", status_code=status.HTTP_200_OK, response_model=ListTripsResponse)
def list_trips_for_user(username: str, db: Session = Depends(get_db)) -> ListTripsResponse:
    """List trips associated with a given username."""
    try:
        return service.list_trips_for_username(db, username)
    except ValueError as e:
        if str(e) == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to list trips")