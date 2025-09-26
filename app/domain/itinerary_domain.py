from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel

from app.domain.booking_domain import HotelInfo, FlightInfo


class Activity(BaseModel):
    """Represents an activity scheduled in an itinerary day."""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: Optional[str] = None  # ISO datetime string
    end_time: Optional[str] = None    # ISO datetime string
    location: Optional[str] = None
    category: Optional[str] = None    # e.g., Sightseeing, Dining, Adventure
    cost_currency: Optional[str] = None
    cost_amount: Optional[float] = None


class DayPlan(BaseModel):
    """A single day within the itinerary, with hotel, flights, and activities."""
    day_number: int
    date: Optional[str] = None  # ISO date string (YYYY-MM-DD)

    # Lodging for the day (if any). Reuse HotelInfo from booking domain.
    hotel: Optional[HotelInfo] = None

    # Flights relevant to this day (departure/arrival segments)
    flights: List[FlightInfo] = []

    # Activities scheduled throughout the day
    activities: List[Activity] = []

    notes: Optional[str] = None


class Itinerary(BaseModel):
    """An itinerary that spans multiple days, each with its own plan."""
    id: Optional[str] = None
    trip_id: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None  # ISO date string
    end_date: Optional[str] = None    # ISO date string

    days: List[DayPlan] = []

    # Optional roll-up fields
    currency: Optional[str] = None
    estimated_total_cost: Optional[float] = None
    travelers: Optional[int] = None

    notes: Optional[str] = None


class ItenaryCreateRequest(BaseModel):
    """Request object to create an itinerary.

    Includes overall configuration like places to visit, number of days,
    date range, and optionally preselected hotels and flights.
    """
    places_to_visit: List[str]
    no_of_days: int
    start_date: str  # ISO date string (YYYY-MM-DD)
    end_date: str    # ISO date string (YYYY-MM-DD)

    # Optional preselected items to seed the itinerary
    hotels: Optional[List[HotelInfo]] = None
    flights: Optional[List[FlightInfo]] = None


class ItineraryUpdateRequest(BaseModel):
    """Partial update payload for an Itinerary (limited fields)."""
    title: Optional[str] = None
    notes: Optional[str] = None


class PlaceInfo(BaseModel):
    """Compact info for a stop in the itinerary sequence."""
    place: str
    distance_to_next: Optional[str] = None
    photo: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    google_map_link: Optional[str] = None
