from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import log_info, log_error
from app.domain.trip_domain import CreateGroupTripRequest, AddUserToTripRequest, AddUserToTripByCodeRequest, CreateTripResponse, ListTripsResponse, JoinTripResponse, TripMembersResponse
from app.services.trip_service import TripService
from app.models.user import User
from app.models.trip import Trip
router = APIRouter(prefix="/trips", tags=["trips"])  # Intentionally empty for MVP

service = TripService()


@router.get("")
def get_trips_root():
    """Root trips endpoint - returns API info."""
    return {
        "message": "Trip Planner API", 
        "endpoints": {
            "POST /trips": "Create a new trip",
            "POST /trips/add-user": "Add user to trip", 
            "GET /trips/by-user/{username}": "List trips for user"
        }
    }


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


@router.post("/join", status_code=status.HTTP_200_OK, response_model=JoinTripResponse)
def add_user_to_trip_by_code(code: str, payload: AddUserToTripByCodeRequest, db: Session = Depends(get_db)) -> JoinTripResponse:
    """Join a trip using a trip code provided as query parameter `code`.

    Example: POST /trips/join?code=123456
    Body: { "user_id": "...", ...optional preferences }
    """
    log_info("add user to trip by code request", trip_code=code, user_id=str(payload.user_id))
    try:
        return service.add_user_to_trip_by_code(db, code, payload)
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


@router.get("/{trip_id}/members", status_code=status.HTTP_200_OK, response_model=TripMembersResponse)
def get_trip_members(trip_id: str, db: Session = Depends(get_db)) -> TripMembersResponse:
    try:
        return service.get_trip_members(db, trip_id)
    except ValueError as e:
        if str(e) == "trip_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trip not found")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to get trip members")