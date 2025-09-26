from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.langgraph.agents.flight_agent import FlightAgent

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/search")
def search_flights(
    origin_code: str = Query(..., description="IATA code e.g., COK"),
    origin_city: str = Query(..., description="City name e.g., Kochi"),
    dest_code: str = Query(..., description="IATA code e.g., BOM"),
    dest_city: str = Query(..., description="City name e.g., Mumbai"),
    date: str = Query("2025-05-01", description="YYYY-MM-DD"),
    cabin: str = Query("Economy"),
    currency: str = Query("INR"),
    travelers: int = Query(1, ge=1),
    format: str = Query("cards", description="'cards' for list cards, 'bookings' for booking-details payloads"),
) -> Dict[str, Any]:
    """Return flight options for a given route.

    - format=cards: UI-ready flight cards
    - format=bookings: Booking Details payloads for the modal
    """
    agent = FlightAgent()

    if format == "bookings":
        data = agent.mock_flight_bookings_for_ui(
            origin_code=origin_code,
            origin_city=origin_city,
            dest_code=dest_code,
            dest_city=dest_city,
            date=date,
            travelers=travelers,
            currency=currency,
        )
        return {"flights": data, "format": "bookings"}

    cards = agent.mock_flight_options_for_ui(
        origin_code=origin_code,
        origin_city=origin_city,
        dest_code=dest_code,
        dest_city=dest_city,
        date=date,
        cabin=cabin,
        currency=currency,
    )
    return {"flights": cards, "format": "cards"}
