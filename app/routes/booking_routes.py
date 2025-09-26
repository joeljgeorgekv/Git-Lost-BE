from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.langgraph.agents.flight_agent import FlightAgent
from app.langgraph.agents.hotel_agent import HotelAgent
from app.routes.itinerary_routes import MOCK_MUMBAI_ITINERARY

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/mock")
def get_all_bookings_mock(
    # Flights
    origin_code: str = Query("COK", description="Origin IATA code e.g., COK"),
    origin_city: str = Query("Kochi", description="Origin city name e.g., Kochi"),
    dest_code: str = Query("BOM", description="Destination IATA code e.g., BOM"),
    dest_city: str = Query("Mumbai", description="Destination city name e.g., Mumbai"),
    flight_date: str = Query("2025-05-01", description="Flight date YYYY-MM-DD"),
    travelers: int = Query(2, ge=1),
    currency: str = Query("INR"),
    cabin: str = Query("Economy"),
    # Hotels
    destination: str = Query("Mumbai"),
    budget_range: str = Query("mid-range"),
    rooms: int = Query(1, ge=1),
    check_in: str = Query("2025-05-01"),
    check_out: str = Query("2025-05-03"),
) -> Dict[str, Any]:
    """Return mock booking payloads only for items present in the itinerary.

    Currently aligned to the provided Mumbai itinerary mock:
      - Flights: Akasa Air QP 1519, SpiceJet SG 132
      - Hotel: Hotel Bawa Continental

    If destination is not Mumbai, all generated items are returned as a fallback.
    """
    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()

    flights = flight_agent.mock_flight_bookings_for_ui(
        origin_code=origin_code,
        origin_city=origin_city,
        dest_code=dest_code,
        dest_city=dest_city,
        date=flight_date,
        travelers=travelers,
        currency=currency,
    )

    hotels = hotel_agent.mock_hotel_bookings_for_ui(
        destination=destination,
        budget_range=budget_range,
        travelers=travelers,
        rooms=rooms,
        check_in=check_in,
        check_out=check_out,
    )

    # If destination is Mumbai, filter to only itinerary-present items
    if (destination or "").strip().lower() == "mumbai":
        desired_flight_codes = {"QP 1519", "SG 132"}
        flights = [f for f in flights if f.get("flight_code") in desired_flight_codes]

        desired_hotel_names = {"Hotel Bawa Continental"}
        hotels = [h for h in hotels if (h.get("hotel_name") in desired_hotel_names)]

    return {
        "flights": flights,
        "hotels": hotels,
        "currency": currency,
    }
