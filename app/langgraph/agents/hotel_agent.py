from __future__ import annotations

from typing import Dict, Any, List

from app.clients.hotel_client import HotelClient
from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import HotelOption


class HotelAgent:
    """Agent responsible for finding and suggesting hotel options."""
    
    def __init__(self):
        self.hotel_client = HotelClient()
    
    def find_hotels(
        self, 
        destination: str, 
        dates: str,
        budget_range: str = "mid-range",
        guests: int = 2
    ) -> List[HotelOption]:
        """Find hotel options for the trip."""
        
        try:
            # Extract check-in and check-out dates
            check_in, check_out = self._extract_dates(dates)
            
            # Search for hotels
            hotel_results = self.hotel_client.search_hotels(
                destination=destination,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                budget_range=budget_range
            )
            
            # Convert to domain objects
            hotel_options = []
            for hotel in hotel_results:
                hotel_option = HotelOption(
                    name=hotel["name"],
                    location=hotel["location"],
                    price_per_night_usd=hotel["price_per_night_usd"],
                    rating=hotel["rating"],
                    amenities=hotel["amenities"],
                    why_matches=hotel["why_matches"],
                    booking_link=hotel.get("booking_link"),
                    photo_url=hotel.get("photo_url")
                )
                hotel_options.append(hotel_option)
            
            # Rank hotels based on preferences
            hotel_options = self._rank_hotels(hotel_options, budget_range)
            
            log_info("Hotel options found", count=len(hotel_options), destination=destination)
            return hotel_options
            
        except Exception as e:
            log_error("Failed to find hotels", error=str(e), destination=destination)
            return self._get_fallback_hotels(destination, budget_range)
    
    def _extract_dates(self, dates: str) -> tuple[str, str]:
        """Extract check-in and check-out dates from date string."""
        try:
            if "-" in dates:
                parts = dates.split("-")
                if len(parts) >= 2:
                    check_in = parts[0].strip()
                    check_out = parts[1].strip()
                    return check_in, check_out
        except:
            pass
        
        # Fallback dates
        return "2025-04-15", "2025-04-18"
    
    def _rank_hotels(self, hotels: List[HotelOption], budget_range: str) -> List[HotelOption]:
        """Rank hotels based on budget preference and rating."""
        
        if budget_range == "budget":
            # Sort by price (ascending), then by rating (descending)
            return sorted(hotels, key=lambda h: (h.price_per_night_usd, -h.rating))
        elif budget_range == "luxury":
            # Sort by rating (descending), then by price (descending)
            return sorted(hotels, key=lambda h: (-h.rating, -h.price_per_night_usd))
        else:  # mid-range
            # Balance price and rating
            return sorted(hotels, key=lambda h: (h.price_per_night_usd / h.rating))
    
    def _get_fallback_hotels(self, destination: str, budget_range: str) -> List[HotelOption]:
        """Return fallback hotel options if search fails."""
        
        price_map = {
            "budget": 45,
            "mid-range": 95,
            "luxury": 250
        }
        
        base_price = price_map.get(budget_range, 95)
        
        if destination.lower() == "bali":
            return [
                HotelOption(
                    name="Ubud Village Resort",
                    location="Ubud",
                    price_per_night_usd=base_price,
                    rating=4.4,
                    amenities=["Pool", "Spa", "Restaurant", "Cultural Tours"],
                    why_matches="Perfect location for cultural exploration with modern amenities",
                    booking_link="https://booking.example.com/hotels/ubud-village",
                    photo_url="https://images.unsplash.com/search/photos/ubud-hotel"
                ),
                HotelOption(
                    name="Seminyak Beach Hotel",
                    location="Seminyak",
                    price_per_night_usd=base_price + 30,
                    rating=4.5,
                    amenities=["Beach Access", "Pool", "Rooftop Bar", "Spa"],
                    why_matches="Great beachfront location with vibrant nightlife nearby",
                    booking_link="https://booking.example.com/hotels/seminyak-beach",
                    photo_url="https://images.unsplash.com/search/photos/seminyak-hotel"
                )
            ]
        else:
            return [
                HotelOption(
                    name=f"{destination} Central Hotel",
                    location="City Center",
                    price_per_night_usd=base_price,
                    rating=4.2,
                    amenities=["WiFi", "Restaurant", "Gym", "Pool"],
                    why_matches=f"Well-located hotel in {destination} with good amenities",
                    booking_link=f"https://booking.example.com/hotels/{destination.lower()}-central",
                    photo_url=f"https://images.unsplash.com/search/photos/{destination.lower()}-hotel"
                )
            ]
