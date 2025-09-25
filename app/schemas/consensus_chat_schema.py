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
