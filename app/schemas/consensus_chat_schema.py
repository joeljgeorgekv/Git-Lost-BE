from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.consensus_schema import ConsensusPayload


class ConsensusChatRequest(BaseModel):
    """Request to drive chat after consensus, with a single latest user message.
    The server can optionally keep the short history for better context.
    """

    # Latest user message and optional recent history
    user_message: str
    messages: List[Dict[str, Any]] = []

    # The consensus payload from the UI
    consensus: ConsensusPayload

    # Optional hints
    origin_city: Optional[str] = None
    needs_flight: Optional[bool] = None  # if None, the service will infer
    passengers: int = 2
    budget_range: Optional[str] = "mid-range"

    # Pagination knobs
    flights_limit: int = 3
    flights_offset: int = 0
    hotels_limit: int = 5
    hotels_offset: int = 0
    cabs_limit: int = 5
    cabs_transfer_offset: int = 0
    cabs_day_offset: int = 0


class FlightOption(BaseModel):
    """Flight option details."""
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[str] = None
    stops: Optional[int] = None


class HotelOption(BaseModel):
    """Hotel option details."""
    name: Optional[str] = None
    rating: Optional[float] = None
    price_per_night: Optional[str] = None
    location: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    why_it_matches: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    type: Optional[str] = None  # Hotel / Resort / Apartment
    price_currency: Optional[str] = None


class CabOption(BaseModel):
    """Cab/transport option details."""
    type: Optional[str] = None  # "transfer", "day_rental", etc.
    provider: Optional[str] = None
    price: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class TripOverview(BaseModel):
    """Trip overview/itinerary details."""
    title: Optional[str] = None
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    duration: Optional[str] = None


class HotelRoomDetails(BaseModel):
    """Detailed room information for the booking modal."""
    type: Optional[str] = None
    bedding: Optional[str] = None
    max_occupancy: Optional[int] = None
    inclusions: List[str] = Field(default_factory=list)
    refund_policy: Optional[str] = None


class HotelPriceBreakdown(BaseModel):
    """Price breakdown for the booking modal (formatted strings allowed)."""
    room_rate_total: Optional[str] = None
    taxes_and_fees: Optional[str] = None
    discounts: Optional[str] = None
    total: Optional[str] = None


class HotelBookingDetails(BaseModel):
    """Booking Details payload for the modal UI."""
    hotel_name: Optional[str] = None
    rating: Optional[float] = None
    location: Optional[str] = None
    image: Optional[str] = None
    gallery: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    stay_check_in: Optional[str] = None  # YYYY-MM-DD
    stay_check_out: Optional[str] = None  # YYYY-MM-DD
    stay_nights: Optional[int] = None
    travelers: Optional[int] = None
    rooms: Optional[int] = None
    room: Optional[HotelRoomDetails] = None
    amenities: List[str] = Field(default_factory=list)
    policies: Dict[str, Any] = Field(default_factory=dict)
    currency: Optional[str] = None
    price_breakdown: Optional[HotelPriceBreakdown] = None


class ConsensusChatResponse(BaseModel):
    """Structured response for consensus chat with specific data types."""
    
    # Core response data
    destination: Optional[str] = None
    dates: Optional[str] = None
    route_taken: Optional[str] = None
    
    # Trip planning options
    trip_overview: Optional[TripOverview] = None
    flight_options: List[FlightOption] = Field(default_factory=list)
    hotel_options: List[HotelOption] = Field(default_factory=list)
    cab_transfer_options: List[CabOption] = Field(default_factory=list)
    cab_day_options: List[CabOption] = Field(default_factory=list)
    # Booking modal payloads
    hotel_booking: Optional[HotelBookingDetails] = None
    
    # AI suggestions and guidance
    suggestions: List[str] = Field(default_factory=list)
    
    # Selected items (if any)
    selected_flight: Optional[FlightOption] = None
    selected_hotel: Optional[HotelOption] = None
    
    # Metadata
    user_message: Optional[str] = None
    origin_city: Optional[str] = None
    budget_range: Optional[str] = None
    passengers: Optional[int] = None
    needs_flight: Optional[bool] = None
