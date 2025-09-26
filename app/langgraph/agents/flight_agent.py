from __future__ import annotations

from typing import Dict, Any, List, Optional

from app.clients.flight_client import FlightClient
from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import FlightOption


class FlightAgent:
    """Agent responsible for finding and suggesting flight options."""
    
    def __init__(self):
        self.flight_client = FlightClient()
    
    def find_flights(
        self, 
        origin_city: str, 
        destination: str, 
        dates: str,
        budget_range: str = "mid-range"
    ) -> List[FlightOption]:
        """Find flight options for the trip."""
        
        try:
            # Get airport codes
            origin_code = self.flight_client.get_airport_code(origin_city)
            dest_code = self.flight_client.get_airport_code(destination)
            
            if not origin_code or not dest_code:
                log_error("Could not find airport codes", origin=origin_city, destination=destination)
                return self._get_fallback_flights(origin_city, destination)
            
            # Extract departure date from dates string (simplified)
            departure_date = self._extract_departure_date(dates)
            
            # Search for flights
            flight_results = self.flight_client.search_flights(
                origin=origin_code,
                destination=dest_code,
                departure_date=departure_date
            )
            
            # Convert to domain objects
            flight_options = []
            for flight in flight_results:
                flight_option = FlightOption(
                    departure_airport=flight["departure_airport"],
                    arrival_airport=flight["arrival_airport"],
                    departure_time=flight["departure_time"],
                    arrival_time=flight["arrival_time"],
                    flight_duration=flight["flight_duration"],
                    estimated_price_usd=flight["estimated_price_usd"],
                    airline=flight["airline"],
                    why_matches=flight["why_matches"],
                    booking_link=flight.get("booking_link")
                )
                flight_options.append(flight_option)
            
            # Sort by price and relevance
            flight_options = self._rank_flights(flight_options, budget_range)
            
            log_info("Flight options found", count=len(flight_options), origin=origin_city, destination=destination)
            return flight_options[:3]  # Return top 3 options
            
        except Exception as e:
            log_error("Failed to find flights", error=str(e), origin=origin_city, destination=destination)
            return self._get_fallback_flights(origin_city, destination)
    
    def _extract_departure_date(self, dates: str) -> str:
        """Extract departure date from date string."""
        # Simplified extraction - in production, use proper date parsing
        try:
            if "-" in dates:
                return dates.split("-")[0].strip()
            return dates.strip()
        except:
            return "2025-04-15"  # Fallback date
    
    def _rank_flights(self, flights: List[FlightOption], budget_range: str) -> List[FlightOption]:
        """Rank flights based on budget preference and other factors."""
        
        if budget_range == "budget":
            # Sort by price (ascending)
            return sorted(flights, key=lambda f: f.estimated_price_usd)
        elif budget_range == "luxury":
            # Sort by airline quality and timing
            return sorted(flights, key=lambda f: (-f.estimated_price_usd, f.departure_time))
        else:  # mid-range
            # Balance price and convenience
            return sorted(flights, key=lambda f: (f.estimated_price_usd, f.departure_time))
    
    def _get_fallback_flights(self, origin: str, destination: str) -> List[FlightOption]:
        """Return fallback flight options if search fails."""
        
        base_price = 400
        if destination.lower() in ["bali", "phuket", "thailand"]:
            base_price = 450
        elif destination.lower() in ["europe", "usa"]:
            base_price = 800
        
        return [
            FlightOption(
                departure_airport="DEL",
                arrival_airport="DPS",
                departure_time="08:30",
                arrival_time="14:00",
                flight_duration="5h 30m",
                estimated_price_usd=base_price,
                airline="IndiGo",
                why_matches="Direct flight with good timing",
                booking_link=f"https://booking.example.com/flights/{origin}-{destination}"
            ),
            FlightOption(
                departure_airport="DEL",
                arrival_airport="DPS",
                departure_time="15:45",
                arrival_time="21:15",
                flight_duration="5h 30m",
                estimated_price_usd=base_price - 50,
                airline="Air Asia",
                why_matches="Budget-friendly afternoon departure",
                booking_link=f"https://booking.example.com/flights/{origin}-{destination}"
            )
        ]

    # ------------------------------
    # UI-oriented mock data helpers
    # ------------------------------
    def mock_flight_options_for_ui(
        self,
        origin_code: str = "DEL",
        origin_city: str = "Delhi",
        dest_code: str = "DPS",
        dest_city: str = "Bali",
        date: str = "2025-10-03",
        cabin: str = "Economy",
        currency: str = "INR",
    ) -> List[Dict[str, Any]]:
        """Return UI-ready mock flight cards.

        Shape matches what a card component needs (times, codes, airline, price, cabin, stops).
        """
        # Kochi -> Mumbai curated set
        if origin_code.upper() == "COK" and dest_code.upper() in ("BOM", "BOM"):
            cards: List[Dict[str, Any]] = [
                {
                    "airline": "Akasa Air",
                    "flight_code": "QP 1519",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "11:50",
                    "arrival_time": "13:55",
                    "duration": "2h 05m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-03",
                    "price_current": "₹4,681" if currency == "INR" else "$56",
                    "price_strike": "₹4,969" if currency == "INR" else "$60",
                },
                {
                    "airline": "SpiceJet",
                    "flight_code": "SG 132",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "17:20",
                    "arrival_time": "19:25",
                    "duration": "2h 05m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-03",
                    "price_current": "₹4,844" if currency == "INR" else "$58",
                    "price_strike": "₹5,434" if currency == "INR" else "$65",
                },
                {
                    "airline": "Air India",
                    "flight_code": "AI 2670",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "22:30",
                    "arrival_time": "00:50 +1",
                    "duration": "2h 20m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-03",
                    "price_current": "₹5,541" if currency == "INR" else "$66",
                    "price_strike": "₹5,881" if currency == "INR" else "$70",
                },
                {
                    "airline": "IndiGo",
                    "flight_code": "6E 662",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "07:55",
                    "arrival_time": "09:50",
                    "duration": "1h 55m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-03",
                    "price_current": "₹5,590" if currency == "INR" else "$67",
                    "price_strike": "₹5,958" if currency == "INR" else "$71",
                },
            ]
            return cards

        # Mumbai -> Kochi curated reverse set (aligned to reference)
        if origin_code.upper() == "BOM" and dest_code.upper() == "COK":
            date = "2025-10-05"
            cards: List[Dict[str, Any]] = [
                {
                    "airline": "SpiceJet",
                    "flight_code": "SG 131",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "14:00",
                    "arrival_time": "16:00",
                    "duration": "2h 00m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-05",
                    "price_current": "₹4,600" if currency == "INR" else "$55",
                    "price_strike": "₹4,900" if currency == "INR" else "$59",
                },
                {
                    "airline": "IndiGo",
                    "flight_code": "6E 6701",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "05:35",
                    "arrival_time": "07:25",
                    "duration": "1h 50m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-05",
                    "price_current": "₹5,389" if currency == "INR" else "$65",
                    "price_strike": "₹5,740" if currency == "INR" else "$69",
                },
                {
                    "airline": "Air India",
                    "flight_code": "AI 2407",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "00:20",
                    "arrival_time": "02:20",
                    "duration": "2h 00m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-05",
                    "price_current": "₹5,468" if currency == "INR" else "$66",
                    "price_strike": "₹5,820" if currency == "INR" else "$70",
                },
                {
                    "airline": "Air India",
                    "flight_code": "AI 2743",
                    "origin_code": origin_code,
                    "origin_city": origin_city,
                    "dest_code": dest_code,
                    "dest_city": dest_city,
                    "departure_time": "05:05",
                    "arrival_time": "07:00",
                    "duration": "1h 55m",
                    "stops": 0,
                    "stops_text": "Non stop",
                    "cabin": cabin,
                    "date": "2025-10-05",
                    "price_current": "₹5,468" if currency == "INR" else "$66",
                    "price_strike": "₹5,820" if currency == "INR" else "$70",
                },
            ]
            return cards

        cards: List[Dict[str, Any]] = [
            {
                "airline": "Air India",
                "flight_code": "AI 314",
                "origin_code": origin_code,
                "origin_city": origin_city,
                "dest_code": dest_code,
                "dest_city": dest_city,
                "departure_time": "14:00",
                "arrival_time": "23:30",
                "duration": "5h 30m",
                "stops": 0,
                "stops_text": "Direct",
                "cabin": cabin,
                "date": date,
                "price_current": "₹18,500" if currency == "INR" else "$225",
                "price_strike": "₹22,000" if currency == "INR" else "$270",
            },
            {
                "airline": "Vistara",
                "flight_code": "UK 971",
                "origin_code": origin_code,
                "origin_city": origin_city,
                "dest_code": dest_code,
                "dest_city": dest_city,
                "departure_time": "09:10",
                "arrival_time": "14:45",
                "duration": "5h 35m",
                "stops": 0,
                "stops_text": "Direct",
                "cabin": cabin,
                "date": date,
                "price_current": "₹19,200" if currency == "INR" else "$235",
                "price_strike": "₹22,500" if currency == "INR" else "$275",
            },
            {
                "airline": "AirAsia",
                "flight_code": "AK 381 + AK 378",
                "origin_code": origin_code,
                "origin_city": origin_city,
                "dest_code": dest_code,
                "dest_city": dest_city,
                "departure_time": "06:30",
                "arrival_time": "15:40",
                "duration": "9h 10m",
                "stops": 1,
                "stops_text": "1 stop via KUL",
                "cabin": cabin,
                "date": date,
                "price_current": "₹15,800" if currency == "INR" else "$190",
                "price_strike": "₹19,500" if currency == "INR" else "$235",
            },
        ]

        return cards

    def mock_flight_bookings_for_ui(
        self,
        origin_code: str = "DEL",
        origin_city: str = "Delhi",
        dest_code: str = "DPS",
        dest_city: str = "Bali",
        date: str = "2025-05-01",
        travelers: int = 1,
        currency: str = "INR",
    ) -> List[Dict[str, Any]]:
        """Return Booking Details payloads for the modal, based on the card mocks.

        Includes savings, total for travelers, and route string.
        """
        cards = self.mock_flight_options_for_ui(
            origin_code=origin_code,
            origin_city=origin_city,
            dest_code=dest_code,
            dest_city=dest_city,
            date=date,
            currency=currency,
        )

        def _to_int(price: str) -> int:
            import re
            digits = re.sub(r"[^0-9]", "", price)
            return int(digits) if digits else 0

        bookings: List[Dict[str, Any]] = []
        for c in cards:
            current = _to_int(c.get("price_current", "0"))
            strike = _to_int(c.get("price_strike", "0"))
            savings = max(strike - current, 0)
            total = current * max(travelers, 1)
            route = f"{c['origin_code']} → {c['dest_code']}"

            bookings.append({
                "airline": c["airline"],
                "flight_code": c["flight_code"],
                "route": route,
                "duration": c["duration"],
                "stops_text": c["stops_text"],
                "date": c["date"],
                "cabin": c["cabin"],
                "price_current": c["price_current"],
                "price_strike": c["price_strike"],
                "savings": (f"₹{savings:,}" if currency == "INR" else f"${savings}") if savings else None,
                "travelers": travelers,
                "total": (f"₹{total:,}" if currency == "INR" else f"${total}"),
                "type": "Flight",
            })

        return bookings
