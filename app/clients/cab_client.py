from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.core.logger import log_info


class CabClient:
    """Mock cab/transfer client providing airport transfers and day cabs."""

    def search_airport_transfers(self, destination: str, dates: str, passengers: int = 2) -> List[Dict[str, Any]]:
        options = [
            {
                "id": "cab-transfer-sedan",
                "name": "Private Sedan Airport Transfer",
                "type": "airport_transfer",
                "capacity": 3,
                "price_usd": 35,
                "vendor": "LocalPartner",
                "why_matches": "Door-to-door transfer to hotel",
                "booking_link": f"https://booking.example.com/cabs/{destination.lower()}-sedan",
            },
            {
                "id": "cab-transfer-van",
                "name": "Private Van Airport Transfer",
                "type": "airport_transfer",
                "capacity": 6,
                "price_usd": 55,
                "vendor": "LocalPartner",
                "why_matches": "Spacious van for groups and luggage",
                "booking_link": f"https://booking.example.com/cabs/{destination.lower()}-van",
            },
        ]
        log_info("cab transfers (mock)", destination=destination, count=len(options))
        return options

    def search_day_cabs(self, destination: str, dates: str, passengers: int = 2) -> List[Dict[str, Any]]:
        options = [
            {
                "id": "cab-day-8h",
                "name": "8-hour Local Day Cab",
                "type": "day_cab",
                "capacity": 4,
                "price_usd": 50,
                "vendor": "CityRides",
                "why_matches": "Flexible full-day hire with driver",
                "booking_link": f"https://booking.example.com/cabs/{destination.lower()}-8h",
            }
        ]
        log_info("cab day-cabs (mock)", destination=destination, count=len(options))
        return options
