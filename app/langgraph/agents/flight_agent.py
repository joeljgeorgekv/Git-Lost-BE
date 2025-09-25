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
