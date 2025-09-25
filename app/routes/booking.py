from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.services.booking_service import BookingService
from app.domain.booking_domain import (
    RoomBookingResponse,
    CabBookingResponse,
    CabBookingRequest,
    HotelSearchItem,
    FlightInfo,
    CabSearchItem,
)

router = APIRouter(prefix="/booking", tags=["booking"]) 

# Initialize service (simple module-level instance; replace with DI if needed later)
service = BookingService()


class RoomBookingRequest(BaseModel):
    """Optional payload for room booking requests."""
    hotel_id: Optional[str] = None
    check_in: Optional[str] = None  # ISO date string
    check_out: Optional[str] = None  # ISO date string
    guests: Optional[int] = None
    room_type: Optional[str] = None


## Using shared CabBookingRequest from domain models


@router.post("/rooms", response_model=RoomBookingResponse)
async def book_room(payload: RoomBookingRequest) -> RoomBookingResponse:
    """Book a hotel room (hardcoded response)."""
    return service.book_room(payload)


@router.post("/cabs", response_model=CabBookingResponse)
async def book_cab(payload: CabBookingRequest) -> CabBookingResponse:
    """Book a cab (hardcoded response)."""
    return service.book_cab(payload)


@router.get("/hotels", response_model=List[HotelSearchItem])
async def get_hotels() -> List[HotelSearchItem]:
    """Fetch a list of hotels (hardcoded)."""
    return service.get_hotels()


@router.get("/flights", response_model=List[FlightInfo])
async def get_flights() -> List[FlightInfo]:
    """Fetch a list of flights (hardcoded)."""
    return service.get_flights()


@router.get("/cabs", response_model=List[CabSearchItem])
async def get_cabs() -> List[CabSearchItem]:
    """Fetch a list of cabs (hardcoded)."""
    return service.get_cabs()
