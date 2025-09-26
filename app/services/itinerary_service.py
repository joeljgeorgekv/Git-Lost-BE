from __future__ import annotations

from typing import List, Optional
from datetime import date, datetime, timedelta

from app.domain.itinerary_domain import (
    ItenaryCreateRequest,
    Itinerary,
    DayPlan,
    Activity,
    PlaceInfo,
)
from app.domain.booking_domain import HotelInfo, FlightInfo
from app.langgraph.graphs.itinerary_generation_fast import ItineraryCreationEngine


class ItineraryService:
    """Service to build itineraries from a creation request.

    Provides a very simple in-memory persistence for demo/testing.
    """

    _store: List[Itinerary] = []
    _id_counter: int = 1

    def _parse_date(self, s: str) -> date:
        return date.fromisoformat(s)

    def _date_str(self, d: date) -> str:
        return d.isoformat()

    def _same_day(self, dt_str: Optional[str], d: date) -> bool:
        if not dt_str:
            return False
        try:
            # FlightInfo.depart_time is ISO datetime string
            dt = datetime.fromisoformat(dt_str)
            return dt.date() == d
        except Exception:
            return False

    def _gen_day_activities(self, day_idx: int, day_date: date, places: List[str]) -> List[Activity]:
        """Generate simple placeholder activities for a given day.

        We rotate through the provided places_to_visit across days and
        create two activities: Morning and Afternoon.
        """
        activities: List[Activity] = []
        if not places:
            return activities

        place = places[day_idx % len(places)]
        iso_date = self._date_str(day_date)
        activities.append(
            Activity(
                title=f"Morning at {place}",
                description=f"Explore key attractions in {place}.",
                start_time=f"{iso_date}T09:00:00",
                end_time=f"{iso_date}T12:00:00",
                location=place,
                category="Sightseeing",
                cost_currency=None,
                cost_amount=None,
            )
        )
        activities.append(
            Activity(
                title=f"Afternoon in {place}",
                description=f"Local food and markets in {place}.",
                start_time=f"{iso_date}T14:00:00",
                end_time=f"{iso_date}T17:00:00",
                location=place,
                category="Dining",
                cost_currency=None,
                cost_amount=None,
            )
        )
        return activities

    def create_itinerary(self, req: ItenaryCreateRequest, use_ai: bool = False) -> Itinerary:
        """Create itinerary by delegating generation to the AI-ready graph, then persist.

        Args:
            req: ItenaryCreateRequest payload
            use_ai: when True, attempts AI-based generation with fallback
        """
        graph = ItineraryCreationGraph()
        itinerary = graph.generate(req, use_ai=use_ai)
        # assign an ID and persist
        itinerary.id = f"IT-{self._id_counter:04d}"
        # keep other optional rollups as-is (graph may fill them later)
        # persist in memory and bump id counter
        ItineraryService._store.append(itinerary)
        ItineraryService._id_counter += 1
        return itinerary

    def list_itineraries(self) -> List[Itinerary]:
        """Return all created itineraries (in-memory)."""
        return list(self._store)

    def get_itinerary(self, itinerary_id: str) -> Optional[Itinerary]:
        for it in self._store:
            if it.id == itinerary_id:
                return it
        return None

    def update_itinerary(self, itinerary_id: str, *, title: Optional[str] = None, notes: Optional[str] = None) -> Optional[Itinerary]:
        it = self.get_itinerary(itinerary_id)
        if not it:
            return None
        if title is not None:
            it.title = title
        if notes is not None:
            it.notes = notes
        return it

    def delete_itinerary(self, itinerary_id: str) -> bool:
        for idx, it in enumerate(self._store):
            if it.id == itinerary_id:
                del self._store[idx]
                return True
        return False

    # New behavior: always-AI place sequence creation returning List[PlaceInfo]
    def create_itinerary_places(self, req: ItenaryCreateRequest) -> List[PlaceInfo]:
        """Generate a PlaceInfo sequence using a fast, resilient engine.

        Uses the fast engine (haversine + nearest-neighbor + realistic durations) to ensure
        responsive results while we stabilize the AI graph. This does not persist state.
        """
        engine = ItineraryCreationEngine()
        return engine.generate_places(req)
