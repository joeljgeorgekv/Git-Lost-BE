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

    # ------------------------------
    # UI-oriented mock data helpers
    # ------------------------------
    def mock_hotel_options_for_ui(self, destination: str, budget_range: str = "mid-range") -> List[Dict[str, Any]]:
        """Return UI-ready mock hotel cards matching consensus_chat_schema.HotelOption fields.
        This does not call providers and is safe for demos.
        """
        hotels = [
            {
                "name": "Hotel Royal Onix",
                "rating": 4.2,
                "price_per_night": "₹2,500",
                "total_price": "₹5,000",
                "price_currency": "INR",
                "location": "Andheri West",
                "amenities": ["Wi‑Fi", "AC Rooms", "Room Service"],
                "image": "https://r2imghtlak.mmtcdn.com/r2-mmt-htl-image/htl-imgs/201604211438269175-53bf7510714811e8bfbf0a148b2efb82.jpg",
                "images": [],
                "badges": ["Great Value"],
                "why_it_matches": ["Comfortable", "Good rating", "Value for money"],
                "summary": "Comfortable mid-tier stay near Andheri West hot spots",
                "type": "Hotel",
            },
            {
                "name": "Hotel Mid-Town",
                "rating": 4.1,
                "price_per_night": "₹2,900",
                "total_price": "₹5,800",
                "price_currency": "INR",
                "location": "Andheri West (near Andheri Station)",
                "amenities": ["Wi‑Fi", "Restaurant", "Airport Shuttle"],
                "image": "https://r2imghtlak.mmtcdn.com/r2-mmt-htl-image/htl-imgs/201506161010244436-c5a1b71c289611ebbc540242ac110002.jpg",
                "images": [],
                "badges": ["Near Station"],
                "why_it_matches": ["Very near Andheri station", "Balanced cost vs comfort"],
                "summary": "Convenient location with balanced comfort and price",
                "type": "Hotel",
            },
            {
                "name": "Hotel Bawa Continental",
                "rating": 4.3,
                "price_per_night": "₹5,500",
                "total_price": "₹11,000",
                "price_currency": "INR",
                "location": "Juhu",
                "amenities": ["Beach Access", "Restaurant", "Concierge"],
                "image": "https://gos3.ibcdn.com/0ba5c43ec4d411e8a5d1023b42bcea16.jfif",
                "images": [],
                "badges": ["Beach Proximity"],
                "why_it_matches": ["Close to Juhu Beach", "Nicer ambience"],
                "summary": "Comfortable stay close to Juhu Beach with pleasant ambience",
                "type": "Hotel",
            },
            {
                "name": "Hotel Lucky",
                "rating": 4.0,
                "price_per_night": "₹3,800",
                "total_price": "₹7,600",
                "price_currency": "INR",
                "location": "Bandra West",
                "amenities": ["Wi‑Fi", "Restaurant"],
                "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0e/d0/14/67/lucky-hotels-and-restaurants.jpg?w=900&h=500&s=1",
                "images": [],
                "badges": ["Good Location"],
                "why_it_matches": ["Decent amenities", "Good Bandra location"],
                "summary": "Reliable option with good Bandra West location",
                "type": "Hotel",
            },
            {
                "name": "Wind Flower Residency",
                "rating": 4.1,
                "price_per_night": "₹3,500",
                "total_price": "₹7,000",
                "price_currency": "INR",
                "location": "Bandra West",
                "amenities": ["Wi‑Fi", "Room Service", "Laundry"],
                "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2a/54/8e/d1/hotel-windflower-regency.jpg?w=900&h=500&s=1",
                "images": [],
                "badges": ["Reliable"],
                "why_it_matches": ["Good mid-tier", "Reliable services"],
                "summary": "Mid-tier stay in Bandra West with dependable services",
                "type": "Hotel",
            },
        ]

        return hotels

    def mock_hotel_bookings_for_ui(
        self,
        destination: str,
        budget_range: str = "mid-range",
        travelers: int = 4,
        rooms: int = 2,
        check_in: str = "2025-10-03",
        check_out: str = "2025-10-05",
    ) -> List[Dict[str, Any]]:
        """Return a list of HotelBookingDetails-shaped dicts for the given destination.

        Maps the mock hotel cards into the booking modal payload schema so the UI can
        render the "Booking Details" dialog directly.
        """
        cards = self.mock_hotel_options_for_ui(destination, budget_range=budget_range)

        def _nights(a: str, b: str) -> int:
            try:
                from datetime import datetime as _dt
                return ( _dt.fromisoformat(b) - _dt.fromisoformat(a) ).days
            except Exception:
                return 5

        stay_n = _nights(check_in, check_out)

        bookings: List[Dict[str, Any]] = []
        for c in cards:
            per_night = c.get("price_per_night") or "₹0/night"
            currency = c.get("price_currency") or ("INR" if per_night.strip().startswith("₹") else "USD")
            # Build HotelBookingDetails-shaped payload
            bookings.append({
                "hotel_name": c.get("name"),
                "rating": c.get("rating"),
                "location": c.get("location"),
                "image": c.get("image"),
                "gallery": c.get("images", []),
                "summary": c.get("summary"),
                "stay_check_in": check_in,
                "stay_check_out": check_out,
                "stay_nights": stay_n,
                "travelers": travelers,
                "rooms": rooms,
                "room": {
                    "type": "Deluxe Room" if c.get("type") != "Hostel" else "Dorm Bed",
                    "bedding": "1 King" if c.get("type") != "Hostel" else "Bunk",
                    "max_occupancy": 2 if c.get("type") != "Hostel" else 1,
                    "inclusions": ["Breakfast", "Free Wi‑Fi"],
                    "refund_policy": "Free cancellation until 48h before check‑in",
                },
                "amenities": c.get("amenities", []),
                "policies": {
                    "check_in": "15:00",
                    "check_out": "11:00",
                    "cancellation": "Free cancellation up to 48h before check‑in",
                },
                "currency": currency,
                "price_breakdown": {
                    "room_rate_total": per_night,
                    "taxes_and_fees": "Included",
                    "discounts": "₹0" if currency == "INR" else "$0",
                    "total": c.get("total_price"),
                },
            })

        return bookings