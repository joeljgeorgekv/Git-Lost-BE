from __future__ import annotations

from typing import List, Optional, Dict
import os
import json

from app.domain.itinerary_domain import ItenaryCreateRequest, PlaceInfo
from app.clients.google_places_client import GooglePlacesClient


class ItineraryCreationEngine:
    """Fast, resilient itinerary place generator.

    - Resolves coordinates for each place.
    - Reorders by nearest-neighbor to reduce travel.
    - Computes distance_to_next via Haversine only (no Distance Matrix).
    - Generates realistic time windows based on distance bands with a lunch gap.
    - Optionally can be extended to use AI for initial ordering; kept off for speed.
    """

    @staticmethod
    def _time_to_minutes(t: str) -> int:
        hh, mm = t.split(":")
        return int(hh) * 60 + int(mm)

    @staticmethod
    def _minutes_to_time(m: int) -> str:
        m = max(0, m)
        hh = (m // 60)
        mm = (m % 60)
        return f"{hh:02d}:{mm:02d}"

    @staticmethod
    def _duration_hours_by_distance_km(km: Optional[float]) -> float:
        if km is None:
            return 2.0
        if km >= 7000:
            return 12.0  # ultra long-haul
        if km >= 2000:
            return 10.0  # long-haul, effectively travel day
        if km >= 1000:
            return 6.0   # inter-country
        if km >= 200:
            return 3.0   # intercity/regional
        return 2.0       # local

    def generate_places(self, req: ItenaryCreateRequest) -> List[PlaceInfo]:
        client = GooglePlacesClient()

        # Fallback geo hints to help resolve ambiguous city names fast
        fallback_geo: Dict[str, str] = {
            "Kakkanad": "Kakkanad, Kerala, India",
            "Pune": "Pune, Maharashtra, India",
            "Kochi": "Kochi, Kerala, India",
            "Tokyo": "Tokyo, Japan",
            "Madrid": "Madrid, Spain",
        }

        # Resolve coordinates and map links; keep original order initially
        resolved = []
        for name in req.places_to_visit:
            info = client.resolve_place(name) or {}
            # If not resolved, try with a geo hint
            if info.get("lat") is None and name in fallback_geo:
                hinted = fallback_geo[name]
                info = client.resolve_place(hinted) or info
            resolved.append({
                "place": name,
                "lat": info.get("lat"),
                "lng": info.get("lng"),
                "map_link": client.get_map_link(name),
            })

        # If nothing resolved, return empty
        if not resolved:
            return []

        # Nearest-neighbor reordering starting from the first
        ordered = [resolved[0]]
        remaining = resolved[1:]
        while remaining:
            last = ordered[-1]
            def dist(p):
                if last.get("lat") is None or p.get("lat") is None:
                    return float("inf")
                return client.haversine_km(last["lat"], last["lng"], p["lat"], p["lng"])
            next_idx = min(range(len(remaining)), key=lambda i: dist(remaining[i]))
            ordered.append(remaining.pop(next_idx))

        # Pre-compute haversine distances to next (one value per stop)
        haversine_kms: List[Optional[float]] = []
        for idx in range(len(ordered)):
            if idx < len(ordered) - 1:
                a, b = ordered[idx], ordered[idx + 1]
                if a.get("lat") is not None and b.get("lat") is not None:
                    haversine_kms.append(
                        client.haversine_km(a["lat"], a["lng"], b["lat"], b["lng"])  # km
                    )
                else:
                    haversine_kms.append(None)
            else:
                haversine_kms.append(None)

        # Build cumulative schedule
        day_start = self._time_to_minutes("08:00")
        day_end = self._time_to_minutes("20:00")
        current_min = day_start
        lunch_start = self._time_to_minutes("13:00")
        lunch_end = self._time_to_minutes("14:00")

        results: List[PlaceInfo] = []
        for idx, item in enumerate(ordered):
            name = item["place"]
            km = haversine_kms[idx] if idx < len(ordered) - 1 else None
            # If km unknown, try to resolve coordinates inline and compute
            if km is None and idx < len(ordered) - 1:
                a = item
                b = ordered[idx + 1]
                if a.get("lat") is None or b.get("lat") is None:
                    ao = client.resolve_place(a["place"]) or {}
                    bo = client.resolve_place(b["place"]) or {}
                    if ao.get("lat") is not None and bo.get("lat") is not None:
                        km = client.haversine_km(ao["lat"], ao["lng"], bo["lat"], bo["lng"])

            hours = self._duration_hours_by_distance_km(km)
            duration_min = int(hours * 60)

            # If this item would exceed the day's end, roll over to next day morning
            if current_min + duration_min > day_end:
                current_min = day_start

            # Respect lunch gap
            if current_min < lunch_start and (current_min + duration_min) > lunch_start:
                current_min = lunch_end

            t_start = self._minutes_to_time(current_min)
            t_end = self._minutes_to_time(current_min + duration_min)
            current_min += duration_min

            # Build photo URL (use hint if needed)
            photo_query = name if name not in fallback_geo else fallback_geo[name]
            photo_url = client.get_first_photo_media_url_for_query(photo_query)

            # Compose distance text
            distance_text = f"{km:.1f} km" if km is not None else None
            results.append(
                PlaceInfo(
                    place=name,
                    distance_to_next=distance_text,
                    photo=photo_url,
                    time_start=t_start,
                    time_end=t_end,
                    google_map_link=item["map_link"],
                )
            )

        return results
