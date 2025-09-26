from __future__ import annotations

from typing import List, Optional
import os
import json

from datetime import date, datetime, timedelta

from app.domain.itinerary_domain import ItenaryCreateRequest, Itinerary, DayPlan, Activity, PlaceInfo
from app.domain.booking_domain import HotelInfo, FlightInfo
from app.clients.google_places_client import GooglePlacesClient
class ItineraryCreationGraph:
    """AI-ready scaffold to create an Itinerary from a request.
    For now, this uses deterministic placeholder logic. It can later be
    replaced to call an LLM/agentic LangGraph that crafts a detailed
    itinerary with richer activities.
    """

    def generate_places(self, req: ItineraryCreateRequest, fast: bool = False) -> List[PlaceInfo]:
        """Generate a PlaceInfo sequence with AI guidance and deterministic safeguards.
        """
        if fast:
            return self._generate_places_fast(req)
        else:
            return self._generate_places(req)

    def _generate_places_fast(self, req: ItineraryCreateRequest) -> List[PlaceInfo]:
        """Generate a PlaceInfo sequence with AI guidance and deterministic safeguards.
        """
        places: List[str] = req.places
        if not places:
            return []

        results: List[PlaceInfo] = []
        current_min = time_to_minutes("09:00")
        for i, (name, distance_text, photo_url, map_link) in enumerate(places):
            duration_min = time_to_minutes("01:00")
            # If current_min is before lunch and activity would overlap lunch, insert lunch break
            lunch_start = time_to_minutes("13:00")
            lunch_end = time_to_minutes("14:00")
            # If we would start before lunch and end after lunch, push start to after lunch
            if current_min < lunch_start and (current_min + duration_min) > lunch_start:
                current_min = lunch_end

            t_start = minutes_to_time(current_min)
            t_end = minutes_to_time(current_min + duration_min)
            current_min += duration_min

            results.append(
                PlaceInfo(
                    place=name,
                    distance_to_next=distance_text,
                    photo=photo_url,
                    time_start=t_start,
                    time_end=t_end,
                    google_map_link=map_link,
                )
            )

        return results

    def _gen_day_activities_ai(self, day_idx: int, day_date: date, places: List[str]) -> Optional[List[Activity]]:
        """Attempt to use OpenAI to generate activities. Returns None if not available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            place = places[day_idx % len(places)] if places else "the destination"
            iso_date = self._date_str(day_date)
            prompt = (
                f"Create two short activities (morning and afternoon) for {place} on {iso_date}. "
                f"Return JSON array with objects: title, description, start_time, end_time, location, category."
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = resp.choices[0].message.content.strip()
            import json

            data = json.loads(content)
            acts: List[Activity] = []
            for item in data[:2]:
                acts.append(
                    Activity(
                        title=item.get("title"),
                        description=item.get("description"),
                        start_time=item.get("start_time"),
                        end_time=item.get("end_time"),
                        location=item.get("location"),
                        category=item.get("category"),
                    )
            t_start = minutes_to_time(current_min)
            t_end = minutes_to_time(current_min + duration_min)
            current_min += duration_min

            results.append(
                PlaceInfo(
                    place=name,
                    distance_to_next=distance_text,
                    photo=photo_url,
                    time_start=t_start,
                    time_end=t_end,
                    google_map_link=map_link,
                )
            )

        return results
