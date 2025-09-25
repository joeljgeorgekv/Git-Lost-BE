from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class PlanningStage(str, Enum):
    PLACE_SUGGESTIONS = "place_suggestions"
    TRIP_OVERVIEW = "trip_overview"
    FLIGHTS = "flights"
    HOTELS = "hotels"
    DETAILED_ITINERARY = "detailed_itinerary"


class PlaceOption(BaseModel):
    """A suggested destination with details."""
    place: str  # e.g., "Bali", "Phuket"
    best_months: List[str]  # e.g., ["April", "May", "September"]
    photo_url: Optional[str] = None
    why_matches: str  # explanation of why it fits the trip
    avg_budget_usd: int  # estimated budget per person
    country: str
    highlights: List[str]  # key attractions/features


class TripOverview(BaseModel):
    """Initial trip plan after place is selected."""
    trip_name: str  # e.g., "Bali Long Weekend"
    destination: str
    dates: str  # e.g., "April 15-18, 2025"
    num_days: int
    day_names: List[str]  # e.g., ["Thursday", "Friday", "Saturday", "Sunday"]
    areas: List["AreaPlan"]  # different areas/regions to visit


class AreaPlan(BaseModel):
    """Plan for a specific area/region."""
    area_name: str  # e.g., "Ubud Cultural Journey"
    what_to_see: List[str]  # e.g., ["Rice terraces", "Waterfalls", "Temples"]
    keywords: List[str]  # e.g., ["Beach", "Sunset", "Dining"]
    estimated_days: float  # e.g., 1.5 days


class FlightOption(BaseModel):
    """Flight suggestion with details."""
    departure_airport: str  # e.g., "DEL"
    arrival_airport: str  # e.g., "DPS"
    departure_time: str
    arrival_time: str
    flight_duration: str  # e.g., "5h 30m"
    estimated_price_usd: int
    airline: str
    why_matches: str  # explanation
    booking_link: Optional[str] = None


class HotelOption(BaseModel):
    """Hotel suggestion with details."""
    name: str
    location: str  # area/neighborhood
    price_per_night_usd: int
    rating: float  # out of 5
    amenities: List[str]
    why_matches: str
    booking_link: Optional[str] = None
    photo_url: Optional[str] = None


class DetailedItineraryDay(BaseModel):
    """Detailed day-by-day itinerary."""
    day: int
    day_name: str  # e.g., "Thursday"
    date: str  # e.g., "April 15, 2025"
    activities: List["Activity"]
    estimated_budget_usd: int


class Activity(BaseModel):
    """Individual activity in the itinerary."""
    time: str  # e.g., "9:00 AM"
    name: str  # e.g., "Visit Tegallalang Rice Terraces"
    location: str
    duration: str  # e.g., "2 hours"
    description: str
    estimated_cost_usd: int
    distance_from_previous: Optional[str] = None  # e.g., "15 minutes by car"
    transport_method: Optional[str] = None  # e.g., "Private car", "Walking"


class TravelPlanningRequest(BaseModel):
    """Request for the travel planning flow."""
    messages: List[Dict[str, Any]]  # chat messages
    previous_summary: Optional[str] = None
    stage: PlanningStage = PlanningStage.PLACE_SUGGESTIONS
    selected_place: Optional[str] = None
    selected_dates: Optional[str] = None
    selected_flight: Optional[str] = None
    selected_hotel: Optional[str] = None
    origin_city: Optional[str] = None  # user's starting location
    budget_range: Optional[str] = None  # e.g., "budget", "mid-range", "luxury"


class TravelPlanningResponse(BaseModel):
    """Response from the travel planning flow."""
    stage: PlanningStage
    summary: str
    
    # Stage-specific responses
    place_suggestions: Optional[List[PlaceOption]] = None
    trip_overview: Optional[TripOverview] = None
    flight_options: Optional[List[FlightOption]] = None
    hotel_options: Optional[List[HotelOption]] = None
    detailed_itinerary: Optional[List[DetailedItineraryDay]] = None
    
    # Metadata
    next_stage: Optional[PlanningStage] = None
    suggestions: List[str] = []  # user guidance
    model: Optional[str] = None
    tokens_used: Optional[int] = None
