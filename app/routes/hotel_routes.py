from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.langgraph.agents.hotel_agent import HotelAgent

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("/search")
def search_hotels(
    destination: str = Query(..., description="City or destination, e.g., 'Jaisalmer'"),
    budget_range: str = Query("mid-range", description="budget | mid-range | luxury"),
    travelers: int = Query(2, ge=1),
    rooms: int = Query(1, ge=1),
    check_in: Optional[str] = Query(None, description="YYYY-MM-DD"),
    check_out: Optional[str] = Query(None, description="YYYY-MM-DD"),
    format: str = Query("cards", description="'cards' for list cards, 'bookings' for booking-details payloads"),
) -> Dict[str, Any]:
    """Return hotel options for a destination.

    - format=cards: UI-ready hotel cards (HotelOption-like dicts)
    - format=bookings: list of HotelBookingDetails-like dicts ready for the booking modal
    """
    agent = HotelAgent()

    if format == "bookings":
        data = agent.mock_hotel_bookings_for_ui(
            destination=destination,
            budget_range=budget_range,
            travelers=travelers,
            rooms=rooms,
            check_in=check_in or "2025-05-01",
            check_out=check_out or "2025-05-06",
        )
        return {"hotels": data, "format": "bookings"}

    # default: cards
    cards = agent.mock_hotel_options_for_ui(destination=destination, budget_range=budget_range)
    return {"hotels": cards, "format": "cards"}
