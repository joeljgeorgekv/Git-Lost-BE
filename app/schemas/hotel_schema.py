from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Stay(BaseModel):
    check_in: str = Field(..., description="YYYY-MM-DD")
    check_out: str = Field(..., description="YYYY-MM-DD")
    nights: Optional[int] = None


class PriceBreakdown(BaseModel):
    room_rate_total: Optional[float] = None
    taxes_and_fees: Optional[float] = None
    discounts: Optional[float] = None


class Price(BaseModel):
    currency: str = Field("USD")
    per_night: Optional[float] = None
    nights: Optional[int] = None
    breakdown: Optional[PriceBreakdown] = None
    total: Optional[float] = None


class Room(BaseModel):
    type: Optional[str] = None
    bedding: Optional[str] = None
    max_occupancy: Optional[int] = None
    inclusions: List[str] = Field(default_factory=list)
    refund_policy: Optional[str] = None


class Location(BaseModel):
    area: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    map_url: Optional[str] = None


class HotelItem(BaseModel):
    id: Optional[str] = None
    name: str
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    badges: List[str] = Field(default_factory=list)
    location: Optional[Location] = None
    images: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    why_it_matches: List[str] = Field(default_factory=list)
    stay: Optional[Stay] = None
    room: Optional[Room] = None
    amenities: List[str] = Field(default_factory=list)
    price: Optional[Price] = None
    booking_link: Optional[str] = None


class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    guests: int = 2
    budget_range: str = Field("mid-range", description="budget | mid-range | luxury")


class HotelSearchResponse(BaseModel):
    hotels: List[HotelItem] = Field(default_factory=list)


class HotelBookingRequest(BaseModel):
    hotel_id: str
    hotel_name: str
    check_in: str
    check_out: str
    travelers: int = 2
    rooms: int = 1
    currency: str = "USD"
    per_night: float


class HotelBookingResponse(BaseModel):
    booking: Dict[str, Any] = Field(default_factory=dict)
